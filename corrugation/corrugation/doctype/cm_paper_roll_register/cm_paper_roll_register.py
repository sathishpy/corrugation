# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class CMPaperRollRegister(Document):
	def autoname(self):
		self.name = self.purchase_invoice + "-roll-register"

	def populate_rolls(self):
		self.purchase_weight = self.get_purchase_weight()
		self.total_weight = 0

		invoice = frappe.get_doc("Purchase Invoice", self.purchase_invoice)
		print("Populating {0} CM Paper Rolls for invoice {1}".format(len(invoice.items), self.purchase_invoice))
		self.paper_rolls = []
		for item in invoice.items:
			if not is_paper_item(item): continue
			weight = item.qty

			rolls = frappe.db.sql_list("""select name from `tabCM Paper Roll` where paper=%s""", item.item_code)
			if rolls:
				idx = len(rolls) + 1
			else:
				idx = 1
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
			paper_roll.weight = roll.weight
			paper_roll.status = "Ready"
			paper_roll.save()

	def get_purchase_weight(self):
		invoice = frappe.get_doc("Purchase Invoice", self.purchase_invoice)
		weight = 0
		for item in invoice.items:
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
def is_paper_item(rm):
	if "paper" in rm.item_name or "Paper" in rm.item_name:
		return True
	return False
