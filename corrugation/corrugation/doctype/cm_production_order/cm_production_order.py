# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.manufacturing.doctype.production_order.production_order import make_stock_entry
from erpnext.stock.utils import get_latest_stock_qty
from corrugation.corrugation.roll_selection import select_rolls_for_box
from corrugation.corrugation.doctype.cm_box_description.cm_box_description import get_planned_paper_quantity
from corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order import update_production_roll_qty
from corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order import update_roll_qty
from corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order import get_used_paper_qunatity_from_rolls
from corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order import set_new_layer_defaults

class CMProductionOrder(Document):
	def autoname(self):
		orders = frappe.db.sql_list("""select name from `tabCM Production Order` where sales_order=%s""", self.sales_order)
		if orders is None:
			self.name = "PO-{0}-{1}".format(self.box, self.sales_order, idx)
		else:
			self.name = "PO-{0}-{1}-{2}".format(self.box, self.sales_order, len(orders))

	def populate_order_items(self):
		if (self.sales_order is None): return
		order_items = frappe.db.sql("""select item_code, qty from `tabSales Order Item`
										where parent='{0}'""".format(self.sales_order), as_dict=1);

		if (len(order_items) > 0):
			selected_item = order_items[0]
			self.box = selected_item.item_code
			self.order_qty = self.mfg_qty = selected_item.qty
			self.stock_qty = get_latest_stock_qty(self.box)
			box_boms = frappe.get_all("CM Box Description", filters={'box': self.box})
			self.box_desc = box_boms[0].name
		return order_items

	def update_box_roll_qty(self):
		update_roll_qty(self)

	def populate_box_source(self):
		if (self.box_desc is None): return
		self.paper_rolls, self.paper_boards = [], []
		print ("Populating {3} for {0} items of {1} having bom {2}".format(self.mfg_qty, self.box, self.box_desc, self.use_boards))
		if (self.use_boards):
			self.populate_box_boards()
		else:
			self.populate_box_rolls()

	def populate_box_rolls(self):
		self.paper_rolls = []
		if (self.manual_entry): return

		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		#Build a new paper item list for this production
		paper_items = []
		for paper_item in box_details.item_papers:
			new_item = next((item for item in paper_items if item.rm == paper_item.rm and item.rm_type == paper_item.rm_type), None)
			if (new_item != None):
				new_item.rm_weight += float(paper_item.rm_weight * self.mfg_qty)
				continue
			new_item = frappe.new_doc("CM Paper Item")
			new_item.rm_type = paper_item.rm_type
			new_item.rm = paper_item.rm
			new_item.rm_weight = float(paper_item.rm_weight * self.mfg_qty)
			paper_items += [new_item]

		selected_rolls = select_rolls_for_box(paper_items)
		for roll_item in selected_rolls:
			print ("Adding roll {0} as {1}".format(roll_item.paper_roll, roll_item.rm_type))
			self.append("paper_rolls", roll_item)

	def populate_box_boards(self):
		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		for board in box_details.get_all_boards():
			print "Adding board item for {0}".format(board)
			new_item = frappe.new_doc("CM Production Board Detail")
			if "Top" in board:
				new_item.layer_type = "Top"
			else:
				new_item.layer_type = "Flute"
			board_item = frappe.get_doc("Item", board)
			new_item.layer = board_item.name
			new_item.stock_qty = get_latest_stock_qty(board_item.name)
			new_item.used_qty = self.mfg_qty/box_details.item_per_sheet
			self.append("paper_boards", new_item)

	def set_new_layer_defaults(self):
		set_new_layer_defaults(self, "Top")

	def replace_paper_with_boards(self, se):
		other_items = [item for item in se.items if "Paper" not in item.item_code]
		se.items = []
		for board in self.paper_boards:
			board_item = frappe.new_doc("Stock Entry Detail")
			board_item.item_code = board.layer
			board_item.qty = board.used_qty
			board_item.s_warehouse = self.source_warehouse
			se.append("items", board_item)

		for item in other_items:
			print ("Re-adding item {0}".format(item.item_code))
			se.append("items", item)

	def update_paper_quantity(self, se):
		if (self.use_boards):
			return self.replace_paper_with_boards(se)

		for item in se.items:
			print ("Updating item {0}".format(item.item_code))
			rm = frappe.get_doc("Item", item.item_code)
			if rm.item_group != "Paper": continue
			qty = get_used_paper_qunatity_from_rolls(self.paper_rolls, rm.name)
			if qty != 0:
				print("Updating item {0} qunatity to {1}".format(rm.name, qty))
				item.qty = qty
		return se

	def update_rm_quantity(self, se):
		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		for item in se.items:
			bom = frappe.get_doc("BOM", box_details.item_bom)
			bom_item = next((bi for bi in bom.items if bi.item_code == item.item_code), None)
			if (bom_item == None): continue
			print ("Updating RM {0} for quantity {1}".format(item.item_code, self.mfg_qty))
			qty = bom_item.qty * self.mfg_qty
			if qty != 0:
				print("Updating item {0} qunatity to {1}".format(item.item_code, qty))
				item.qty = qty
		return se

	def on_submit(self):
		check_material_availability(self)
		submit_sales_order(self.sales_order)
		submit_production_order(self)
		create_new_stock_entry(self)

def submit_production_order(cm_po):
	po = frappe.new_doc("Production Order")
	po.production_item = cm_po.box
	box_details = frappe.get_doc("CM Box Description", cm_po.box_desc)
	po.bom_no = box_details.item_bom
	po.sales_order = cm_po.sales_order
	po.skip_transfer = True
	po.qty = cm_po.mfg_qty
	po.wip_warehouse = po.source_warehouse = cm_po.source_warehouse
	po.fg_warehouse = cm_po.target_warehouse
	po.submit()
	print "Created production order {0} for {1} of quantity {2}".format(po.name, po.production_item, po.qty)

def submit_sales_order(sales_order):
	order_doc = frappe.get_doc("Sales Order", sales_order)
	if (order_doc.status == 'Draft'):
		order_doc.submit()

@frappe.whitelist()
def create_new_stock_entry(cm_po):
	orders = frappe.get_all("Production Order", fields={"production_item":cm_po.box, "sales_order":cm_po.sales_order})
	if len(orders) > 0:
		po = frappe.get_doc("Production Order", orders[0].name)
	else: frappe.throw("Unable to find the production order for sales_order {0}".format(cm_po.sales_order))

	print "Creating stock entry for production order {0} of quantity {1}".format(po.name, po.qty)

	se = frappe.new_doc("Stock Entry")
	stock_entry = make_stock_entry(po.name, "Manufacture", po.qty)
	se.update(stock_entry)

	cm_po.update_rm_quantity(se)
	cm_po.update_paper_quantity(se)
	se.calculate_rate_and_amount()
	for item in se.items:
		print "Item:{0} Quantity:{1}".format(item.item_code, item.qty)
	se.submit()

	update_production_roll_qty(cm_po)

@frappe.whitelist()
def check_material_availability(cm_po):
	#try to use the stock_entry functionality
	pass

@frappe.whitelist()
def make_new_purchase_order(source_name):
	po = frappe.get_doc("CM Production Order", source_name)
	box_details = frappe.get_doc("CM Box Description", po.box_desc)
	bom = frappe.get_doc("BOM", box_details.item_bom)
	print("Creating PO for CM Order {0}".format(po.name))

	po = frappe.new_doc("Purchase Order")

	for item in bom.items:
		po_item = frappe.new_doc("Purchase Order Item")
		po_item.item_code = item.item_code
		po_item.item_name = item.item_name
		po_item.uom = item.stock_uom
		po_item.description = "Raw materials needed for production {0}".format(source_name)
		po.append("items", po_item)

	return po.as_dict()
