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
		self.new_transaction_items = []

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
				bank_entry.party_type = "Supplier" if not entry["Deposits"].strip() else "Customer"
				party_list = frappe.get_all(bank_entry.party_type, fields=["name"])
				parties = [party.name for party in party_list]
				matches = difflib.get_close_matches(bank_entry.description.lower(), parties, 1, 0.4)
				if len(matches) > 0: bank_entry.party = matches[0]
				print("Finding {0} in {1}".format(bank_entry.description.lower(), bank_entry.party))
				amount = entry["Withdrawals"] if not entry["Deposits"].strip() else entry["Deposits"]
				bank_entry.amount = float(amount)

	def populate_matching_invoices(self):
		self.payment_invoice_items = []
		for entry in self.new_transaction_items:
			if (not entry.party): continue
			account = self.receivable_account if entry.party_type == "Customer" else self.payable_account
			outstanding_invoices = get_outstanding_invoices(entry.party_type, entry.party, account)
			sorted(outstanding_invoices, key=lambda k: k['posting_date'])
			amount = entry.amount
			matching_invoices = []
			for e in outstanding_invoices:
				ent = self.append('payment_invoice_items', {})
				ent.invoice_date = e.get('posting_date')
				ent.invoice_type = "Sales Invoice" if entry.party_type == "Customer" else "Purchase Invoice"
				ent.payment_description = entry.description
				ent.invoice = e.get('voucher_no')
				ent.outstanding_amount = e.get('outstanding_amount')
				ent.allocated_amount = min(float(e.get('invoice_amount')), amount)
				amount -= float(e.get('invoice_amount'))
				matching_invoices += [ent.invoice]
				if (amount <= 0): break

			order_doctype = "Sales Order" if entry.party_type=="Customer" else "Purchase Order"
			from erpnext.controllers.accounts_controller import get_advance_payment_entries
			payment_entries = get_advance_payment_entries(entry.party_type, entry.party, account, order_doctype, against_all_orders=True)
			payment = next((payment for payment in payment_entries if payment.amount == entry.amount), None)
			if (payment is None): continue
			doc = frappe.get_doc(payment.reference_type, payment.reference_name)
			added = next((entry.payment_entry for entry in self.payment_items if entry.payment_entry == doc.name), None)
			if added is not None: continue
			invoices = [entry.invoice for entry in doc.references]
			self.append('payment_items', {"payment_type": doc.doctype,
											"payment_entry": doc.name,
											'party_type': entry.party_type,
											"mode_of_payment": doc.mode_of_payment,
											"reference": doc.reference_no,
											"invoice_type": "Sales Invoice" if entry.party_type == "Customer" else "Purchase Invoice",
											"account": account,
											"invoices": ",".join(invoices + matching_invoices),
											"paid_amount": doc.paid_amount
										})
			entry.reference_name = payment.reference_name
			entry.reference_type = payment.reference_type

	def create_payment_entries(self):
		for payment_entry in self.new_transaction_items:
			if (not payment_entry.party): continue
			print("Creating payment entry for {0}".format(payment_entry.description))
			payment = self.make_customer_payment(payment_entry)
			invoices = [entry.invoice for entry in payment.references if entry is not None]
			self.append('payment_items', {"payment_type": payment.doctype,
											"payment_entry": payment.name,
											"mode_of_payment": payment.mode_of_payment,
											'party_type': payment_entry.party_type,
											"reference": payment.reference_no,
											"invoices": ",".join(invoices),
											"paid_amount": payment.paid_amount
										})
			payment_entry.reference_name = payment.name
			payment_entry.reference_type = payment.doctype
		msgprint(_("Successfully created payment entries"))

	def make_customer_payment(self, pe):
		payment = frappe.new_doc("Payment Entry")
		payment.posting_date = pe.transaction_date
		payment.payment_type = "Receive" if pe.party_type == "Customer" else "Pay"
		payment.mode_of_payment = "Wire Transfer"
		payment.party_type = pe.party_type
		payment.party = pe.party
		payment.paid_to = self.bank_account if pe.party_type == "Customer" else self.payable_account
		payment.paid_from = self.receivable_account if pe.party_type == "Customer" else self.bank_account
		payment.paid_amount = payment.received_amount = pe.amount
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

	def update_payment_entry(self, payment):
		lst = []
		invoices = payment.invoices.split(',')
		for invoice in invoices:
			lst.append(frappe._dict({
				'voucher_type': payment.payment_type,
				'voucher_no' : payment.payment_entry,
				'against_voucher_type' : payment.invoice_type,
				'against_voucher'  : invoice,
				'account' : payment.account,
				'party_type': payment.party_type,
				'party': frappe.get_value("Payment Entry", payment.payment_entry, "party"),
				'unadjusted_amount' : 0,
				'allocated_amount' : float(payment.paid_amount)
			}))
		if lst:
			from erpnext.accounts.utils import reconcile_against_document
			reconcile_against_document(lst)

	def submit_payment_entries(self):
		for payment in self.payment_items:
			doc = frappe.get_doc(payment.payment_type, payment.payment_entry)
			if doc.docstatus == 1:
				self.update_payment_entry(payment)
			else:
				doc.reference_no = payment.reference
				doc.mode_of_payment = payment.mode_of_payment
				doc.save()
				doc.submit()

		for entry in self.new_transaction_items:
			if entry.reference_type is not None:
				self.remove(entry)
				self.append('reconciled_transaction_items', entry)
