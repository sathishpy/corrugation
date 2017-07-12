# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from corrugation.corrugation.doctype.cm_production_order.cm_production_order import select_rolls_for_box

class CMBoardProductionOrder(Document):
	def autoname(self):
		items = frappe.db.sql_list("""select name from `tabCM Board Production Order` where box=%s""", self.box)
		if items: idx = len(items) + 1
		else: idx = 1
		self.name = "CORR-ORDER-" + self.box + ('-%.3i' % idx)

	def populate_rolls(self):
		self.paper_rolls = []
		paper_items = []
		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		for paper_item in box_details.item_papers:
			if (self.layer_type == "Top" and paper_item.rm_type != "Top"): continue
			if (self.layer_type == "Flute" and paper_item.rm_type == "Top"): continue
			new_item = frappe.new_doc("CM Paper Item")
			new_item.rm_type = paper_item.rm_type
			new_item.rm = paper_item.rm
			new_item.rm_weight = float(paper_item.rm_weight * self.mfg_qty * box_details.item_per_sheet)
			paper_items += [new_item]

		selected_rolls = select_rolls_for_box(paper_items)
		for roll_item in selected_rolls:
			print("Selected roll " + roll_item.paper_roll)
			self.append("paper_rolls", roll_item)

	def on_submit(self):
		item = frappe.new_doc("Item")
		box_desc = frappe.get_doc("CM Box Description", self.box_desc)
		item.item_code = item.item_name = "{0}-{1}-{2}".format(self.layer_type, box_desc.sheet_length, box_desc.sheet_width)
		item.item_group = "Board"
		item.valuation_rate = 1
		item.opening_stock = self.mfg_qty
		item.save()
