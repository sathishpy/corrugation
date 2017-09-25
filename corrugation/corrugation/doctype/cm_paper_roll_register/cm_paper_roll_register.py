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

	def populate_papers(self):
		if (self.purchase_receipt is None): return
		receipt = frappe.get_doc("Purchase Receipt", self.purchase_receipt)
		self.roll_count_items = []
		for item in receipt.items:
			if (frappe.db.get_value("Item", item.item_code, "item_group") != "Paper"): continue
			roll_count_item = frappe.new_doc("CM Paper Roll Count Item")
			roll_count_item.paper = item.item_code
			roll_count_item.count = receipt.qty/500
			self.append("roll_count_items", roll_count_item)

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
		for paper_item in self.roll_count_items:
			for i in range(0, paper_item.count):
				paper_roll = frappe.new_doc("CM Paper Roll Detail")
				paper_roll.paper = paper_item.paper
				paper_roll.number = idx
				idx += 1
				(basic, tax, charge) = item_rates[paper_roll.paper]
				paper_roll.unit_cost = (basic + charge)
				self.append("paper_rolls", paper_roll)
				print "Creating Roll {0}-{1}".format(paper_item.paper, paper_roll.weight)

	def renumber_rolls(self):
		if (len(self.paper_rolls) == 0): return
		roll_num = int(self.paper_rolls[0].number)
		for roll_item in self.paper_rolls:
			roll_item.number = roll_num
			roll_num += 1

	def get_item_extra_charges(self, items):
		qty, charges = 0, 0
		for item in items:
			qty += item.qty
		for item in self.charges:
			charges += item.amount
		if (qty != self.purchase_weight):
			print("Purchase weight is {0} and item weight is {1}".format(self.purchase_weight, qty))
		return (charges * float(qty)/self.purchase_weight)

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

		charges += self.get_item_extra_charges(bill_doc.items)

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
			if (roll_item.paper not in item_rates): continue

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
		self.purchase_invoice = pi.name
		self.save()
		#Update the cost only after setting the invoice
		self.update_roll_cost()

	def get_purchase_weight(self):
		receipt = frappe.get_doc("Purchase Receipt", self.purchase_receipt)
		weight = 0
		for item in receipt.items:
			if frappe.db.get_value("Item", item.item_code, "item_group") != "Paper": continue
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

	def on_update(self):
		self.total_weight = 0
		for paper_roll in self.paper_rolls:
			self.total_weight += paper_roll.weight

	def before_submit(self):
		self.total_weight = self.get_roll_weight()
		self.purchase_weight = self.get_purchase_weight()
		if (self.purchase_weight != self.total_weight):
			frappe.throw(_("Paper roll weight doesn't match the purchase weight"))
		self.register_rolls()

	def on_trash(self):
		for roll in self.paper_rolls:
			roll_name = "{0}-RL-{1}".format(roll.paper, roll.number)
			if (frappe.db.get_value("CM Paper Roll", roll_name) == None): break
			paper_roll = frappe.get_doc("CM Paper Roll", roll_name)
			print ("Deleting roll {0}".format(paper_roll.name))
			paper_roll.delete()
		docs = frappe.get_doc("Purchase Receipt", self.purchase_receipt)
		for invoice in [self.purchase_invoice, self.purchase_invoice_2, self.purchase_invoice_3]:
			if (invoie is None): continue
			docs += frappe.get_doc("Purchase Invoice", invoice)
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
	new_register.populate_papers()
	new_register.save(ignore_permissions=True)

def find_roll_receipt_matching_invoice(pi):
	pi_items = [item for item in pi.items if (frappe.db.get_value("Item", item.item_code, "item_group") == "Paper")]
	if (pi_items is None or len(pi_items) == 0): return (None, False)

	open_roll_receipts = frappe.get_all("CM Paper Roll Register", filters={"purchase_invoice": None})
	for receipt in open_roll_receipts:
		print("Checking receipt {0}".format(receipt))
		roll_reg = frappe.get_doc("CM Paper Roll Register", receipt)
		pr = frappe.get_doc("Purchase Receipt", roll_reg.purchase_receipt)
		if (pi.supplier != pr.supplier): continue
		pr_items = [item for item in pr.items if (frappe.db.get_value("Item", item.item_code, "item_group") == "Paper")]
		match = 0
		for idx in range(0, len(pi_items)):
			pr_item = next((item for item in pr_items if item.item_code == pi_items[idx].item_code), None)
			if (pr_item is not None and pi_items[idx].qty == pr_item.qty):
				match += 1
		if (match == len(pi_items)): return (roll_reg, len(pr_items) == len(pi_items))

@frappe.whitelist()
def update_invoice(pi, method):
	print("Updating roll register for doc {0}".format(pi.name))
	(roll_receipt, full_match) = find_roll_receipt_matching_invoice(pi)
	if (roll_receipt == None):
		print("Failed to find the roll receipt for invoice {0}".format(pi.name))
		return
	roll_receipt.update_invoice(pi)
	if (not full_match):
		pr = frappe.get_doc("Purchase Receipt", roll_receipt.purchase_receipt)
		pr_items = [item for item in pr.items if (frappe.db.get_value("Item", item.item_code, "item_group") == "Paper")]
		pi_items = []
		for invoice in [roll_receipt.purchase_invoice, roll_receipt.purchase_invoice_2, roll_receipt.purchase_invoice_3]:
			if invoice is None: continue
			pi = frappe.get_doc("Purchase Invoice", invoice)
			pi_items += [item for item in pi.items if (frappe.db.get_value("Item", item.item_code, "item_group") == "Paper")]
		if (len(pi_items) != len(pr_items)):
			roll_receipt.purchase_invoice_3 = roll_receipt.purchase_invoice_2
			roll_receipt.purchase_invoice_2 = roll_receipt.purchase_invoice
			roll_receipt.purchase_invoice = None
			roll_receipt.save()
