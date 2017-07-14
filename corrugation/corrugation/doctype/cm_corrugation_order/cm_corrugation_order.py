# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from corrugation.corrugation.doctype.cm_production_order.cm_production_order import select_rolls_for_box
from corrugation.corrugation.doctype.cm_production_order.cm_production_order import update_production_roll_qty
from frappe import _

class CMCorrugationOrder(Document):
	def autoname(self):
		items = frappe.db.sql_list("""select name from `tabCM Corrugation Order` where box=%s""", self.box)
		if items: idx = len(items) + 1
		else: idx = 1
		self.name = "CORR-ORDER-" + self.box + ('-%.3i' % idx)

	def populate_rolls(self):
		paper_items, self.paper_rolls = [], []
		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		for paper_item in box_details.item_papers:
			if ("Top" in self.layer_type and paper_item.rm_type != "Top"): continue
			if ("Flute" in self.layer_type and paper_item.rm_type == "Top"): continue
			new_item = frappe.new_doc("CM Paper Item")
			new_item.rm_type = paper_item.rm_type
			new_item.rm = paper_item.rm
			new_item.rm_weight = float(paper_item.rm_weight * self.mfg_qty * box_details.item_per_sheet)
			paper_items += [new_item]

		selected_rolls = select_rolls_for_box(paper_items)
		for roll_item in selected_rolls:
			print("Selected roll " + roll_item.paper_roll)
			self.append("paper_rolls", roll_item)

		self.board_name = box_details.get_board_name(self.get_layer_number())

	def get_layer_number(self):
		roll_item = next((roll_item for roll_item in self.paper_rolls if roll_item.rm_type != "Flute"), None)
		roll = frappe.get_doc("CM Paper Roll", roll_item.paper_roll)
		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		layer = 1
		for paper_item in box_details.item_papers:
			if (paper_item.rm_type == roll_item.rm_type and roll.paper == paper_item.rm): return layer
			layer += 1
		frappe.throw("Failed to find the layer number")

	def get_layer_papers(self):
		papers = [frappe.get_doc("CM Paper Roll", roll_item.paper_roll).paper for roll_item in self.paper_rolls]
		papers = list(set(papers))
		return papers

	def on_update(self):
		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		self.board_name = box_details.get_board_name(self.get_layer_number())

	def on_submit(self):
		self.create_new_stock_entry()
		update_production_roll_qty(self)

	def create_new_stock_entry(self):
		print "Creating stock entry for corrugation order {0} of quantity {1}".format(self.box, self.mfg_qty)
		se = frappe.new_doc("Stock Entry")
		se.purpose = "Manufacture"
		for paper in self.get_layer_papers():
			stock_item = frappe.new_doc("Stock Entry Detail")
			stock_item.item_code = paper
			stock_item.qty = get_used_paper_qunatity_from_rolls(self.paper_rolls, paper)
			stock_item.s_warehouse = frappe.db.get_value("Warehouse", filters={"warehouse_name": _("Stores")})
			se.append("items", stock_item)
		board_item = frappe.new_doc("Stock Entry Detail")
		board_item.item_code = self.board_name
		board_item.qty = self.mfg_qty
		board_item.t_warehouse = frappe.db.get_value("Warehouse", filters={"warehouse_name": _("Stores")})
		se.append("items", board_item)
		se.calculate_rate_and_amount()
		se.submit()

	def submit_production_order(self):
		po = frappe.new_doc("Production Order")
		po.production_item = self.box
		po.bom_no = po.bom
		#po.sales_order = cm_po.sales_order
		po.skip_transfer = True
		po.qty = cm_po.mfg_qty
		store = frappe.db.get_value("Warehouse", filters={"warehouse_name": _("Stores")})
		po.wip_warehouse = po.source_warehouse = po.fg_warehouse = store
		po.submit()
		print "Created production order {0} for corrugation of {1}, quantity:{2}".format(po.name, co.box, po.qty)

@frappe.whitelist()
def get_used_paper_qunatity_from_rolls(paper_rolls, paper):
	box_rolls = {}
	for roll_item in paper_rolls:
		ri = box_rolls.get(roll_item.paper_roll)
		if (ri == None):
			box_rolls[roll_item.paper_roll] = roll_item
		else:
			if (roll_item.final_weight > ri.final_weight):
				ri.start_weight = roll_item.start_weight
				box_rolls[ri.paper] = ri
			else:
				box_rolls[ri.paper] = roll_item
				roll_item.start_weight = ri.start_weight

	qty = 0
	for (key, roll_item) in box_rolls.items():
		roll = frappe.get_doc("CM Paper Roll", roll_item.paper_roll)
		if roll.paper != paper: continue
		qty += (roll_item.start_weight - roll_item.final_weight)
		print("Weight of roll {0} is {1}".format(roll_item.paper_roll, qty))
	return qty
