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

class CMPaymentManager(Document):
	def autoname(self):
		if (self.bank_statement):
			if (not self.from_date or not self.to_date):
				frappe.throw("Enter from and to date for bank statement entries")
			self.name = self.bank_account + "-" + self.from_date + "-" + self.to_date
		else:
			self.name = self.bank_account + nowdate()

	def populate_payment_entries(self):
		if self.bank_statement is None: return
		filename = self.bank_statement.split("/")[-1]
		filepath = frappe.get_site_path("private", "files", filename);
		if (not os.path.isfile(filepath)):
			filepath = frappe.get_site_path("public", "files", filename);

		with open(filepath) as csvfile:
			entries = csv.DictReader(csvfile)
			self.payment_entry_items = []
			for entry in entries:
				print("Processing entry DESC:{0}-W:{1}-D:{2}".format(entry["Particulars"], entry["Withdrawals"], entry["Deposits"]))
				date = entry["Date"]
				if (not date): continue
				bank_entry = frappe.new_doc("CM Payment Entry Item")
				bank_entry.transaction_date = datetime.strptime(date, '%d-%m-%Y').date()
				if (self.from_date and bank_entry.transaction_date < datetime.strptime(self.from_date, '%Y-%m-%d').date()): continue
				if (self.to_date and bank_entry.transaction_date > datetime.strptime(self.to_date, '%Y-%m-%d').date()): continue
				bank_entry.description = entry["Particulars"]
				bank_entry.party_type = "Supplier" if not entry["Deposits"].strip() else "Customer"
				amount = entry["Withdrawals"] if not entry["Deposits"].strip() else entry["Deposits"]
				print("Type: {0} amount:{1}".format(bank_entry.party_type, amount))
				bank_entry.amount = float(amount)
				self.append("payment_entry_items", bank_entry)

	def populate_matching_invoices(self):
		self.payment_invoice_items = []
		for entry in self.payment_entry_items:
			if (not entry.party): continue
			account = self.receivable_account if entry.party_type == "Customer" else self.payable_account
			outstanding_invoices = get_outstanding_invoices(entry.party_type, entry.party, account)
			sorted(outstanding_invoices, key=lambda k: k['posting_date'])
			amount = entry.amount
			for e in outstanding_invoices:
				ent = self.append('payment_invoice_items', {})
				ent.invoice_date = e.get('posting_date')
				ent.invoice_type = "Sales Invoice" if entry.party_type == "Customer" else "Purchase Invoice"
				ent.payment_description = entry.description
				ent.invoice = e.get('voucher_no')
				ent.outstanding_amount = e.get('outstanding_amount')
				ent.allocated_amount = min(float(e.get('invoice_amount')), amount)
				amount -= float(e.get('invoice_amount'))
				if (amount <= 0): break

	def create_payment_entries(self):
		for payment_entry in self.payment_entry_items:
			if (not payment_entry.party): continue
			print("Creating payment entry for {0}".format(payment_entry.description))
			self.make_customer_payment(payment_entry)

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

	def on_update(self):
		self.populate_payment_entries()
		#self.populate_matching_invoices()
