# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PaperRollRegister(Document):
	def autoname(self):
		self.name = self.cm_purchase_invoice + "-roll-register"

	def populate_rolls(self):
		self.cm_purchase_weight = self.get_purchase_weight()

		invoice = frappe.get_doc("Purchase Invoice", self.cm_purchase_invoice)
		print("Populating {0} paper rolls for invoice {1}".format(len(invoice.items), self.cm_purchase_invoice))
		self.cm_paper_rolls = []
		for item in invoice.items:
			weight = item.qty
			while (weight > 0):
				weight -= 500
				paper_roll = frappe.new_doc("Paper Roll Item")
				paper_roll.cm_item = item.item_code
				paper_roll.cm_weight = 500
				self.append("cm_paper_rolls", paper_roll)
				self.cm_total_weight += paper_roll.cm_weight
				print "Creating Roll {0}-{1}".format(item.item_code, item.qty)

	def register_rolls(self):
		for roll in self.cm_paper_rolls:
			paper_roll = frappe.new_doc("Paper Roll")
			paper_roll.cm_item = roll.cm_item
			paper_roll.cm_weight = roll.cm_weight
			paper_roll.save()

	def get_purchase_weight(self):
		invoice = frappe.get_doc("Purchase Invoice", self.cm_purchase_invoice)
		weight = 0
		for item in invoice.items:
			weight += item.qty
		return weight

	def get_roll_weight(self):
		weight = 0
		for roll in self.cm_paper_rolls:
			weight += roll.cm_weight
		return weight

	def on_update(self):
		self.cm_total_weight = self.get_roll_weight()

	def on_submit(self):
		roll_weight = self.get_roll_weight()
		purchase_weight = self.get_purchase_weight()
		if (roll_weight != purchase_weight):
			frappe.throw(_("Paper roll weight doesn't match the purchase weight"))
