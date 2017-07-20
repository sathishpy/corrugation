# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class CMPaperRollRegister(Document):
	def autoname(self):
		self.name = self.purchase_receipt + "-roll-register"

	def populate_rolls(self):
		self.total_weight, self.purchase_weight = 0, self.get_purchase_weight()
		receipt = frappe.get_doc("Purchase Receipt", self.purchase_receipt)

		last_idx = frappe.db.count("CM Paper Roll")
		idx = last_idx + 1
		print("Populating {0} Paper items for receipt {1} starting {2}".format(len(receipt.items), self.purchase_receipt, idx))
		self.paper_rolls = []

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
				self.append("paper_rolls", paper_roll)
				self.total_weight += paper_roll.weight
				print "Creating Roll {0}-{1}".format(item.item_code, paper_roll.weight)

	def register_rolls(self):
		for roll in self.paper_rolls:
			paper_roll = frappe.new_doc("CM Paper Roll")
			paper_roll.paper = roll.paper
			paper_roll.number = roll.number
			paper_roll.weight = roll.weight
			paper_roll.purchase_receipt = self.purchase_receipt
			paper_roll.status = "Ready"
			paper_roll.save()

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

	def on_submit(self):
		roll_weight = self.get_roll_weight()
		purchase_weight = self.get_purchase_weight()
		if (roll_weight != purchase_weight):
			frappe.throw(_("Paper roll weight doesn't match the purchase weight"))
		self.register_rolls()

@frappe.whitelist()
def create_new_rolls(doc, method):
	print("Creating new roll register for doc {0}".format(doc.name))
	new_register = frappe.new_doc("CM Paper Roll Register")
	new_register.purchase_receipt = doc.name
	new_register.populate_rolls()
	new_register.save(ignore_permissions=True)
