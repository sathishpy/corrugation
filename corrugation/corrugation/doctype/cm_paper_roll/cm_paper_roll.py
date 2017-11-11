# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from corrugation.corrugation.doctype.cm_box_description.cm_box_description import get_item_rate

class CMPaperRoll(Document):
	def autoname(self):
		self.name = "{0}-RL-{1}".format(self.paper, self.number)

	def get_unit_rate(self, exclude_tax=True):
		roll_rate = self.basic_cost + self.misc_cost
		if (roll_rate == 0):
			return get_item_rate(self.paper, exclude_tax)
		if (not exclude_tax):
			roll_rate += self.tax_cost
		return roll_rate

	def scrap_paper(self, qty):
		qty = min(qty, self.weight)
		self.weight -= qty
		se = frappe.new_doc("Stock Entry")
		se.purpose = "Repack"
		stock_item = frappe.new_doc("Stock Entry Detail")
		stock_item.item_code = self.paper
		stock_item.qty = qty
		stock_item.s_warehouse = frappe.db.get_value("Warehouse", filters={"warehouse_name": _("Stores")})
		se.append("items", stock_item)
		se.calculate_rate_and_amount()
		se.submit()
