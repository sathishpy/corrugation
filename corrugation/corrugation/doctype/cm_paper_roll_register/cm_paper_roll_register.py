# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate

class CMPaperRollRegister(Document):
	def autoname(self):
		self.name = self.purchase_receipt + "-roll-register"

	def populate_rolls(self):
		if (self.purchase_receipt is None): return
		self.total_weight, self.purchase_weight = 0, self.get_purchase_weight()
		receipt = frappe.get_doc("Purchase Receipt", self.purchase_receipt)

		last_idx = frappe.db.count("CM Paper Roll")
		idx = last_idx + 1
		roll_name = frappe.db.get_value("CM Paper Roll", filters={"number": idx})
		while (roll_name is not None):
			idx = idx + 1
			roll_name = frappe.db.get_value("CM Paper Roll", filters={"number": idx})

		self.supplier = receipt.supplier
		print("Populating {0} Paper items for receipt {1} starting {2} from {3}".format(len(receipt.items), self.purchase_receipt, idx, receipt.supplier))
		self.paper_rolls, self.charges = [], []

		item_rates = self.get_actual_roll_rates()
		for item in receipt.items:
			item_doc = frappe.get_doc("Item", item.item_name)
			if item_doc.item_group != "Paper": continue

			weight = item.qty
			while (weight > 0):
				paper_roll = frappe.new_doc("CM Paper Roll Detail")
				paper_roll.paper = item.item_code
				paper_roll.number = idx
				idx += 1
				if (weight > 500):
					paper_roll.weight = 500
					weight -= 500
				else:
					paper_roll.weight = weight
					weight = 0
				(basic, tax, charge) = item_rates[paper_roll.paper]
				paper_roll.unit_cost = (basic + charge)
				self.append("paper_rolls", paper_roll)
				self.total_weight += paper_roll.weight
				print "Creating Roll {0}-{1}".format(item.item_code, paper_roll.weight)

	def get_actual_roll_rates(self):
		bill_doc = frappe.get_doc("Purchase Receipt", self.purchase_receipt)
		if (self.purchase_invoice):
			bill_doc = frappe.get_doc("Purchase Invoice", self.purchase_invoice)
		item_rates = {}
		std_cost = taxes = charges = 0

		for item in bill_doc.items:
			if frappe.db.get_value("Item", item.item_code, "item_group") != "Services": continue
			charges += item.amount

		std_cost = (bill_doc.total - charges - bill_doc.discount_amount)
		if (self.purchase_invoice):
			 std_cost = std_cost - bill_doc.write_off_amount

		for item in bill_doc.taxes:
			account_type = frappe.db.get_value("Account", item.account_head, "account_type")
			if (account_type == "Tax"):
				taxes += item.tax_amount
			else:
				charges += item.tax_amount

		for item in self.charges:
			charges += item.amount

		print("Rate for {0}: Basic={1} Tax={2} Charges={3}".format(bill_doc.name, std_cost, taxes, charges))
		for item in bill_doc.items:
			if frappe.db.get_value("Item", item.item_code, "item_group") == "Services": continue
			unit_share = float(item.amount/std_cost)/item.qty
			item_rates[item.item_name] = (round(std_cost * unit_share, 3), round(taxes * unit_share, 3), round(charges * unit_share, 3))
			print ("Item {0}:{1}".format(item.item_name, item_rates[item.item_name]))
		return item_rates

	def update_roll_cost(self):
		item_rates = self.get_actual_roll_rates()

		for roll_item in self.paper_rolls:
			roll_name = "{0}-RL-{1}".format(roll_item.paper, roll_item.number)
			if (frappe.db.get_value("CM Paper Roll", roll_name) == None): continue
			roll = frappe.get_doc("CM Paper Roll", roll_name)

			(basic, tax, charge) = item_rates[roll_item.paper]
			if (roll.basic_cost == basic and roll.misc_cost == charge and roll.tax_cost == tax): continue

			print("Old Rates-{0}: Basic={1} Tax={2} Charge={3}".format(roll.name, roll.basic_cost, roll.tax_cost, roll.misc_cost))
			print("New Rates-{0}: Basic={1} Tax={2} Charge={3}".format(roll_name, basic, tax, charge))

			roll_item.unit_cost = (basic + charge)
			roll_item.save()

			roll.basic_cost = basic
			roll.tax_cost = tax
			roll.misc_cost = charge
			roll.save()

	def register_rolls(self):
		item_rates = self.get_actual_roll_rates()

		for roll in self.paper_rolls:
			paper_roll = frappe.new_doc("CM Paper Roll")
			paper_roll.paper = roll.paper
			paper_roll.number = roll.number
			paper_roll.weight = roll.weight
			paper_roll.roll_receipt = self.name
			paper_roll.supplier = self.supplier
			paper_roll.manufacturer = self.manufacturer
			(basic, tax, charge) = item_rates[roll.paper]
			paper_roll.basic_cost = basic
			paper_roll.tax_cost = tax
			paper_roll.misc_cost = charge
			paper_roll.status = "Ready"
			paper_roll.save()

	def update_invoice(self, pi):
		if (len(self.charges) > 0):
			jentry = frappe.new_doc("Journal Entry")
			jentry.update({"voucher_type": "Journal Entry", "posting_date": nowdate(), "is_opening": "No", "remark": "Purchase Charges"})
			for item in self.charges:
				jentry.append("accounts", {"account": item.from_account, "credit_in_account_currency": item.amount})
				jentry.append("accounts", {"account": item.to_account, "debit_in_account_currency": item.amount})
			jentry.submit()
			print("Sumitted journal entry {0}".format(jentry.name))
			self.charge_entry = jentry.name

		self.purchase_invoice = pi.name
		self.save()
		#Update the cost only after setting the invoice
		self.update_roll_cost()

	def get_purchase_weight(self):
		receipt = frappe.get_doc("Purchase Receipt", self.purchase_receipt)
		weight = 0
		for item in receipt.items:
			weight += item.qty
		return weight

	def get_roll_weight(self):
		weight = 0
		for roll in self.paper_rolls:
			weight += roll.weight
		return weight

	def on_validate(self):
		receipt = frappe.get_doc("Purchase Receipt", self.purchase_receipt)
		items = [item.item_code for item in receipt.items]
		for roll in self.paper_rolls:
			if roll.paper not in items:
				frappe.throw("Paper {0} from roll {1} is not present in purchase receipt".format(roll.paper, roll.number))

	def on_submit(self):
		roll_weight = self.get_roll_weight()
		purchase_weight = self.get_purchase_weight()
		if (roll_weight != purchase_weight):
			frappe.throw(_("Paper roll weight doesn't match the purchase weight"))
		self.register_rolls()

	def on_update_after_submit(self):
		pass

	def on_trash(self):
		for roll in self.paper_rolls:
			roll_name = "{0}-RL-{1}".format(roll.paper, roll.number)
			if (frappe.db.get_value("CM Paper Roll", roll_name) == None): break
			paper_roll = frappe.get_doc("CM Paper Roll", roll_name)
			print ("Deleting roll {0}".format(paper_roll.name))
			paper_roll.delete()
		docs = frappe.get_doc("Purchase Invoice", self.purchase_invoice)
		docs += frappe.get_doc("Purchase Receipt", self.purchase_receipt)
		docs += frappe.get_doc("Journal Entry", self.charge_entry)
		for doc in docs:
			print ("Deleting entry {0}".format(doc.name))
			doc.cancel()
			doc.delete()

@frappe.whitelist()
def create_new_rolls(doc, method):
	pr_items = [item for item in doc.items if (frappe.db.get_value("Item", item.item_code, "item_group") == "Paper")]
	if (pr_items is None or len(pr_items) == 0): return
	print("Creating new roll register for doc {0}".format(doc.name))
	new_register = frappe.new_doc("CM Paper Roll Register")
	new_register.purchase_receipt = doc.name
	new_register.populate_rolls()
	new_register.save(ignore_permissions=True)

def find_roll_receipt_matching_invoice(pi):
	open_roll_receipts = frappe.get_all("CM Paper Roll Register", filters={"purchase_invoice": None})
	for receipt in open_roll_receipts:
		print("Checking receipt {0}".format(receipt))
		roll_reg = frappe.get_doc("CM Paper Roll Register", receipt)
		pr = frappe.get_doc("Purchase Receipt", roll_reg.purchase_receipt)
		if (pi.supplier != pr.supplier): continue
		pr_items = [item for item in pr.items if (frappe.db.get_value("Item", item.item_code, "item_group") == "Paper")]
		pi_items = [item for item in pi.items if (frappe.db.get_value("Item", item.item_code, "item_group") == "Paper")]
		if (len(pr_items) != len(pi_items)): continue
		match = True
		for idx in range(0, len(pi_items)):
			if (pi_items[idx].item_code != pr_items[idx].item_code or pi_items[idx].qty != pr_items[idx].qty):
				match = False
				break
		if (match): return roll_reg

@frappe.whitelist()
def update_invoice(pi, method):
	print("Updating roll register for doc {0}".format(pi.name))
	roll_receipt = find_roll_receipt_matching_invoice(pi)
	if (roll_receipt == None):
		print("Failed to find the roll receipt for invoice {0}".format(pi.name))
		return
	roll_receipt.update_invoice(pi)
