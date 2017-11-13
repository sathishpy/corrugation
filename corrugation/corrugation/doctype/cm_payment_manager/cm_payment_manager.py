# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.accounts.utils import get_outstanding_invoices
from frappe.utils import nowdate
from datetime import datetime
import csv, os, re
import difflib

class CMPaymentManager(Document):
	def autoname(self):
		self.name = self.bank_account + "-" + self.from_date + "-" + self.to_date
		self.reconciled_transaction_items = self.new_transaction_items = []
		mapper_name = self.bank_account + "-Mappings"
		if not frappe.db.exists("CM Bank Account Mapper", mapper_name):
			mapper  = frappe.new_doc("CM Bank Account Mapper")
			mapper.bank_account = self.bank_account
			mapper.save()
		self.bank_data_mapper = mapper_name

	def on_update(self):
		if (not self.bank_statement):
			self.reconciled_transaction_items = self.new_transaction_items = []
			return

		if len(self.new_transaction_items + self.reconciled_transaction_items) == 0:
			self.populate_payment_entries()
		else:
			self.move_reconciled_entries()

	def populate_payment_entries(self):
		if self.bank_statement is None: return
		filename = self.bank_statement.split("/")[-1]
		filepath = frappe.get_site_path("private", "files", filename);
		if (not os.path.isfile(filepath)):
			filepath = frappe.get_site_path("public", "files", filename);
		if (len(self.new_transaction_items + self.reconciled_transaction_items) > 0):
			frappe.throw("Transactions already retreived from the statement")

		with open(filepath) as csvfile:
			entries = csv.DictReader(csvfile)
			for entry in entries:
				date = entry["Date"].strip()
				if (not date): continue
				transaction_date = datetime.strptime(date, '%d-%m-%Y').date()
				if (self.from_date and transaction_date < datetime.strptime(self.from_date, '%Y-%m-%d').date()): continue
				if (self.to_date and transaction_date > datetime.strptime(self.to_date, '%Y-%m-%d').date()): continue
				print("Processing entry DESC:{0}-W:{1}-D:{2}-DT:{3}".format(entry["Particulars"], entry["Withdrawals"], entry["Deposits"], entry["Date"]))
				bank_entry = self.append('new_transaction_items', {})
				bank_entry.transaction_date = transaction_date
				bank_entry.description = entry["Particulars"]
				mapped_item = None
				if self.bank_data_mapper:
					mapped_items = frappe.get_doc("CM Bank Account Mapper", self.bank_data_mapper).mapped_items
					mapped_item = next((entry for entry in mapped_items if entry.mapping_type == "Transaction" and entry.bank_data.lower() in bank_entry.description.lower()), None)
				if (mapped_item is not None):
					bank_entry.party_type = mapped_item.mapped_data_type
					bank_entry.party = mapped_item.mapped_data
				else:
					bank_entry.party_type = "Supplier" if not entry["Deposits"].strip() else "Customer"
					party_list = frappe.get_all(bank_entry.party_type, fields=["name"])
					parties = [party.name for party in party_list]
					matches = difflib.get_close_matches(bank_entry.description.lower(), parties, 1, 0.4)
					if len(matches) > 0: bank_entry.party = matches[0]
				print("Finding {0} in {1}".format(bank_entry.description.lower(), bank_entry.party))
				bank_entry.amount = -float(entry["Withdrawals"]) if not entry["Deposits"].strip() else float(entry["Deposits"])

	def populate_matching_invoices(self):
		self.payment_invoice_items = []
		self.map_unknown_transactions()
		added_payments = []
		for entry in self.new_transaction_items:
			if (not entry.party or entry.party_type == "Account"): continue
			account = self.receivable_account if entry.party_type == "Customer" else self.payable_account
			outstanding_invoices = get_outstanding_invoices(entry.party_type, entry.party, account)
			sorted(outstanding_invoices, key=lambda k: k['posting_date'])
			amount = abs(entry.amount)
			matching_invoices = []
			for e in outstanding_invoices:
				ent = self.append('payment_invoice_items', {})
				ent.invoice_date = e.get('posting_date')
				ent.payment_description = entry.description
				ent.party_type = entry.party_type
				ent.party = entry.party
				ent.invoice_type = "Sales Invoice" if entry.party_type == "Customer" else "Purchase Invoice"
				ent.invoice = e.get('voucher_no')
				ent.outstanding_amount = e.get('outstanding_amount')
				ent.allocated_amount = min(float(e.get('invoice_amount')), amount)
				amount -= float(e.get('invoice_amount'))
				matching_invoices += [ent.invoice_type + "|" + ent.invoice]
				if (amount <= 0): break

			amount = abs(entry.amount)
			order_doctype = "Sales Order" if entry.party_type=="Customer" else "Purchase Order"
			from erpnext.controllers.accounts_controller import get_advance_payment_entries
			payment_entries = get_advance_payment_entries(entry.party_type, entry.party, account, order_doctype, against_all_orders=True)
			payment = next((payment for payment in payment_entries if payment.amount == amount and payment not in added_payments), None)
			if (payment is None):
				print("Failed to find payments for {0}:{1}".format(entry.party, amount))
				continue
			added_payments += [payment]
			doc = frappe.get_doc(payment.reference_type, payment.reference_name)
			invoices = [entry.reference_doctype + "|" + entry.reference_name for entry in doc.references]
			entry.reference_name = payment.reference_name
			entry.reference_type = payment.reference_type
			entry.mode_of_payment = "Wire Transfer"
			entry.account = account
			entry.invoices = ",".join(invoices + matching_invoices)
		self.populate_matching_vouchers()

	def map_unknown_transactions(self):
		for entry in self.new_transaction_items:
			if (entry.party): continue
			
	def populate_matching_vouchers(self):
		for entry in self.new_transaction_items:
			if (not entry.party or entry.reference_name): continue
			print("Finding matching voucher for {0}".format(entry.description))
			amount = abs(entry.amount)
			invoices = []
			vouchers = get_matching_journal_entries(self.from_date, self.to_date, entry.party, self.bank_account, amount)
			if len(vouchers) == 0: continue
			for voucher in vouchers:
				added = next((entry.invoice for entry in self.payment_invoice_items if entry.invoice == voucher.voucher_no), None)
				if (added):
					print("Found voucher {0}".format(added))
					continue
				print("Adding voucher {0} {1} {2}".format(voucher.voucher_no, voucher.posting_date, voucher.debit))
				ent = self.append('payment_invoice_items', {})
				ent.invoice_date = voucher.posting_date
				ent.invoice_type = "Journal Entry"
				ent.invoice = voucher.voucher_no
				ent.payment_description = entry.description
				ent.allocated_amount = max(voucher.debit, voucher.credit)

				invoices += [ent.invoice_type + "|" + ent.invoice]
				entry.reference_type = "Journal Entry"
				entry.mode_of_payment = "Wire Transfer"
				entry.reference_name = ent.invoice
				#entry.account = entry.party
				entry.invoices = ",".join(invoices)
				break


	def create_payment_entries(self):
		for payment_entry in self.new_transaction_items:
			if (not payment_entry.party): continue
			if (payment_entry.reference_name): continue
			print("Creating payment entry for {0}".format(payment_entry.description))
			if (payment_entry.party_type == "Account"):
				payment = self.create_journal_entry(payment_entry)
				invoices = [payment.doctype + "|" + payment.name]
				payment_entry.invoices = ",".join(invoices)
			else:
				payment = self.create_payment_entry(payment_entry)
				invoices = [entry.reference_doctype + "|" + entry.reference_name for entry in payment.references if entry is not None]
				payment_entry.invoices = ",".join(invoices)
				payment_entry.mode_of_payment = payment.mode_of_payment
				payment_entry.account = self.receivable_account if payment_entry.party_type == "Customer" else self.payable_account
			payment_entry.reference_name = payment.name
			payment_entry.reference_type = payment.doctype
		msgprint(_("Successfully created payment entries"))

	def create_payment_entry(self, pe):
		payment = frappe.new_doc("Payment Entry")
		payment.posting_date = pe.transaction_date
		payment.payment_type = "Receive" if pe.party_type == "Customer" else "Pay"
		payment.mode_of_payment = "Wire Transfer"
		payment.party_type = pe.party_type
		payment.party = pe.party
		payment.paid_to = self.bank_account if pe.party_type == "Customer" else self.payable_account
		payment.paid_from = self.receivable_account if pe.party_type == "Customer" else self.bank_account
		payment.paid_amount = payment.received_amount = abs(pe.amount)
		payment.reference_no = pe.description
		payment.reference_date = pe.transaction_date
		payment.save()
		for inv_entry in self.payment_invoice_items:
			if (pe.description != inv_entry.payment_description): continue
			reference = payment.append("references", {})
			reference.reference_doctype = inv_entry.invoice_type
			reference.reference_name = inv_entry.invoice
			reference.allocated_amount = inv_entry.allocated_amount
			print ("Adding invoice {0} {1}".format(reference.reference_name, reference.allocated_amount))
		payment.setup_party_account_field()
		payment.set_missing_values()
		#payment.set_exchange_rate()
		#payment.set_amounts()
		#print("Created payment entry {0}".format(payment.as_dict()))
		payment.save()
		return payment

	def create_journal_entry(self, pe):
		je = frappe.new_doc("Journal Entry")
		je.is_opening = "No"
		je.voucher_type = "Bank Entry"
		je.remark = pe.description
		je.posting_date = pe.transaction_date
		if (pe.amount < 0):
			je.append("accounts", {"account": pe.party, "debit_in_account_currency": pe.amount * -1})
			je.append("accounts", {"account": self.bank_account, "credit_in_account_currency": pe.amount * -1})
		else:
			je.append("accounts", {"account": pe.party, "credit_in_account_currency": pe.amount})
			je.append("accounts", {"account": self.bank_account, "debit_in_account_currency": pe.amount})

	def update_payment_entry(self, payment):
		if (payment.reference_type == "Journal Entry"): return
		lst = []
		invoices = payment.invoices.split(',')
		amount = float(abs(payment.amount))
		for invoice_entry in invoices:
			invs = invoice_entry.split('|')
			invoice_type, invoice = invs[0], invs[1]
			outstanding_amount = frappe.get_value(invoice_type, invoice, 'outstanding_amount')

			lst.append(frappe._dict({
				'voucher_type': payment.reference_type,
				'voucher_no' : payment.reference_name,
				'against_voucher_type' : invoice_type,
				'against_voucher'  : invoice,
				'account' : payment.account,
				'party_type': payment.party_type,
				'party': frappe.get_value("Payment Entry", payment.reference_name, "party"),
				'unadjusted_amount' : float(amount),
				'allocated_amount' : min(outstanding_amount, amount)
			}))
			amount -= outstanding_amount
		if lst:
			from erpnext.accounts.utils import reconcile_against_document
			reconcile_against_document(lst)

	def submit_payment_entries(self):
		for payment in self.new_transaction_items:
			if payment.reference_name is None: continue
			doc = frappe.get_doc(payment.reference_type, payment.reference_name)
			if doc.docstatus == 1:
				print("Reconciling payment {0}".format(payment.reference_name))
				self.update_payment_entry(payment)
			else:
				print("Submitting payment {0}".format(payment.reference_name))
				if (payment.reference_type == "Payment Entry"):
					doc.reference_no = payment.payment_reference
					doc.mode_of_payment = payment.mode_of_payment
				doc.save()
				doc.submit()
		self.move_reconciled_entries()

	def move_reconciled_entries(self):
		idx = 0
		while idx < len(self.new_transaction_items):
			entry = self.new_transaction_items[idx]
			print("Indx = {0} lengh={1} entry={2}".format(idx, len(self.new_transaction_items), entry.description))
			idx += 1
			if entry.reference_name is None: continue
			doc = frappe.get_doc(entry.reference_type, entry.reference_name)
			if doc.docstatus == 1 and (entry.reference_type == "Journal Entry" or doc.unallocated_amount == 0):
				self.remove(entry)
				self.append('reconciled_transaction_items', entry)
				idx -= 1


def get_matching_journal_entries(from_date, to_date, account, against, amount):
	query = """select voucher_no, posting_date, account, against, debit_in_account_currency as debit, credit_in_account_currency as credit
							      from `tabGL Entry`
								  where posting_date between '{0}' and '{1}' and account = '{2}' and against = '{3}' and debit = '{4}'
								  """.format(from_date, to_date, account, against, amount)
	jv_entries = frappe.db.sql(query, as_dict=True)
	#print("voucher query:{0}\n Returned {1} entries".format(query, len(jv_entries)))
	return jv_entries
