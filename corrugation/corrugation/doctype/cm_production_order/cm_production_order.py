# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.manufacturing.doctype.production_order.production_order import make_stock_entry
from erpnext.stock.utils import get_latest_stock_qty
from corrugation.corrugation.doctype.cm_box_description.cm_box_description import get_planned_paper_quantity

class CMProductionOrder(Document):
	def autoname(self):
		orders = frappe.db.sql_list("""select name from `tabCM Production Order` where sales_order=%s""", self.sales_order)
		if orders is None:
			self.name = "PO-{0}-{1}".format(self.box, self.sales_order, idx)
		else:
			self.name = "PO-{0}-{1}-{2}".format(self.box, self.sales_order, len(orders))

	def populate_order_items(self):
		if (self.sales_order is None): return
		order_items = self.get_all_order_items();
		if (len(order_items) > 0):
			selected_item = order_items[0]
			self.box = selected_item.item_code
			self.sales_order_qty = self.mfg_qty = selected_item.qty
			self.stock_qty = get_latest_stock_qty(self.box)
			box_boms = frappe.get_all("CM Box Description", filters={'box': self.box})
			self.box_desc = box_boms[0].name
		return order_items

	def update_box_roll_qty(self):
		added_rolls = []
		for roll_item in self.paper_rolls:
			rm_type = roll_item.rm_type
			planned_qty = get_planned_paper_quantity(self.box_desc, rm_type, self.mfg_qty)
			used_roll = get_prod_used_roll(added_rolls, roll_item.paper_roll, rm_type)
			print ("Amount of {0} paper {1} needed is {2}".format(rm_type, roll_item.paper_roll, planned_qty))
			if used_roll is None:
				roll = frappe.get_doc("CM Paper Roll", roll_item.paper_roll)
				roll_item.start_weight = roll.weight
			else:
				roll_item.start_weight = used_roll.est_final_weight

			if (planned_qty < roll_item.start_weight):
				roll_item.est_final_weight = (roll_item.start_weight - planned_qty)
			else:
				roll_item.est_final_weight = 0
			added_rolls += [roll_item]

	def populate_box_source(self):
		if (self.box_desc is None): return
		self.paper_rolls, self.paper_boards = [], []
		print ("Populating {3} for {0} items of {1} having bom {2}".format(self.mfg_qty, self.box, self.box_desc, self.source_type))
		if (self.source_type == "Roll"):
			self.populate_box_rolls()
		else:
			self.populate_box_boards()

	def populate_box_rolls(self):
		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		self.bom = box_details.item_bom
		self.paper_rolls = []
		#Build a new paper item list for this production
		paper_items = []
		for paper_item in box_details.item_papers:
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
			new_item.est_qty = self.mfg_qty/box_details.item_per_sheet
			new_item.used_qty = self.mfg_qty/box_details.item_per_sheet
			self.append("paper_boards", new_item)

	def get_paper_quantity(self, paper):
		#Prepare a list removing identical rolls
		return

	def get_paper_quantity_from_boards(self, paper):
		weight = 0
		for board in self.paper_boards:
			paper_elements = paper.split("-")
			bname = "-" + paper_elements[2] + "-" + paper_elements[3] + "-" + paper_elements[4]
			if bname in board.layer:
				bitem = frappe.get_doc("Item", board.layer)
				weight += bitem.net_weight * board.used_qty
		return weight

	def get_all_order_items(self):
		items = frappe.db.sql("""select item_code, qty from `tabSales Order Item`
								where parent='{0}'""".format(self.sales_order), as_dict=1);
		return items

	def update_paper_from_boards(self, se):
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
		if (self.source_type == "Board"):
			return self.update_paper_from_boards(se)

		for item in se.items:
			print ("Updating item {0}".format(item.item_code))
			rm = frappe.get_doc("Item", item.item_code)
			if rm.item_group != "Paper": continue
			qty = get_used_paper_qunatity_from_rolls(self.paper_rolls, rm.name)
			if qty != 0:
				print("Updating item {0} qunatity to {1}".format(rm.name, qty))
				item.qty = qty
		return se

	def on_submit(self):
		check_material_availability(self)
		submit_sales_order(self.sales_order)
		submit_production_order(self)
		create_new_stock_entry(self)

@frappe.whitelist()
def select_rolls_for_box(paper_items):
	added_rolls, available_rolls = [], []
	#build the unique list
	papers = [pi.rm for pi in paper_items]
	papers = list(set(papers))

	for paper_name in papers:
		rolls = frappe.get_all("CM Paper Roll", fields={"paper" : paper_name})
		available_rolls += rolls
		#print("Found {0} rolls for paper {1}".format(len(rolls), paper_name))

	for paper in paper_items:
		planned_qty = paper.rm_weight
		print "{0} Paper {1} needed: {2}".format(paper.rm_type, paper.rm, planned_qty)
		# Select all the rolls needed to manufacture required quantity
		while planned_qty > 0:
			roll = get_suitable_roll(paper.rm, paper.rm_type, planned_qty, added_rolls, available_rolls)

			if roll is None:
				frappe.throw("Failed to find a roll of weight {0} for paper {1}".format(planned_qty, paper.rm))
				break
			print "Selected Roll is {0} Weight {1}".format(roll.name, roll.weight)

			roll_item = frappe.new_doc("CM Production Roll Detail")
			roll_item.rm_type = paper.rm_type
			roll_item.paper_roll = roll.name
			roll_item.start_weight = roll.weight

			if (roll.weight > planned_qty):
				roll_item.est_final_weight = roll.weight - planned_qty
				planned_qty = 0
			else:
				roll_item.est_final_weight = 0
				planned_qty -= roll.weight

			roll_item.final_weight = roll_item.est_final_weight
			added_rolls += [roll_item]
			available_rolls = [rl for rl in available_rolls if rl.name != roll.name]
	return added_rolls

def get_smallest_roll(paper, rolls):
	weight = 100000
	small_roll = None
	for p_roll in rolls:
		roll = frappe.get_doc("CM Paper Roll", p_roll.name)
		if (roll.status != "Ready" or roll.paper != paper): continue
		if (roll.weight < weight and roll.weight > 10):
			small_roll = roll
			weight = roll.weight
	return small_roll

def get_roll_matching_weight(paper, weight, available_rolls):
	difference = 100000
	matching_roll = None
	for p_roll in available_rolls:
		roll = frappe.get_doc("CM Paper Roll", p_roll.name)
		if (roll.status != "Ready" or roll.paper != paper or roll.weight <= 10): continue
		weight_difference = (roll.weight - weight)
		if (weight_difference < difference or difference < 0):
			matching_roll = roll
			difference = weight_difference
	return matching_roll

def get_suitable_roll(paper, paper_type, weight, added_rolls, available_rolls):
	roll = get_prod_used_roll(added_rolls, paper, paper_type)
	if roll != None: return roll
	if (paper_type != "Top"):
		roll = get_roll_matching_weight(paper, weight, available_rolls)
	else:
		roll = get_smallest_roll(paper, available_rolls)
	return roll

@frappe.whitelist()
def get_prod_used_roll(rolls, paper, rm_type):
	reuse_roll = None
	for p_roll in rolls:
		roll = frappe.get_doc("CM Paper Roll", p_roll.paper_roll)
		if roll.paper != paper: continue
		#Flute and bottom paper used simultaneosuly, so can't be shared
		sharing_conflict = False
		if (p_roll.rm_type == "Flute" and rm_type == "Liner"): sharing_conflict = True
		# Handle duplicate entries of shared rolls
		if (sharing_conflict):
			if (reuse_roll != None and reuse_roll.name == roll.name):
				reuse_roll = None
			continue

	 	print("Found roll {0} of weight {1} for {2}".format(p_roll.paper_roll, p_roll.est_final_weight, rm_type))
		if (reuse_roll != None and reuse_roll.name == roll.name):
			if p_roll.est_final_weight < 10:
				reuse_roll = None
				continue
		if p_roll.est_final_weight > 10:
			reuse_roll = roll
			reuse_roll.weight = p_roll.est_final_weight
	# Update the weight, but don't save it
	return reuse_roll

def update_rm_quantity(po, se):
	for item in se.items:
		bom = frappe.get_doc("BOM", po.bom)
		bom_item = next((bi for bi in bom.items if bi.item_code == item.item_code), None)
		if (bom_item == None): continue
		print ("Updating RM {0} for quantity {1}".format(item.item_code, po.mfg_qty))
		qty = bom_item.qty * po.mfg_qty
		if qty != 0:
			print("Updating item {0} qunatity to {1}".format(item.item_code, qty))
			item.qty = qty
	return se

def submit_production_order(cm_po):
	po = frappe.new_doc("Production Order")
	po.production_item = cm_po.box
	po.bom_no = cm_po.bom
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
def update_production_roll_qty(cm_po):
	for roll_item in cm_po.paper_rolls:
		roll = frappe.get_doc("CM Paper Roll", roll_item.paper_roll)
		roll.status = "Ready"
		roll.weight = roll_item.final_weight
		roll.save()

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

	update_rm_quantity(cm_po, se)
	for item in se.items:
		print "Item:{0} Quantity:{1}".format(item.item_code, item.qty)
	cm_po.update_paper_quantity(se)
	se.calculate_rate_and_amount()
	se.submit()

	update_production_roll_qty(cm_po)

@frappe.whitelist()
def check_material_availability(cm_po):
	#try to use the stock_entry functionality
	pass

@frappe.whitelist()
def make_new_purchase_order(source_name):
	po = frappe.get_doc("CM Production Order", source_name)
	bom = frappe.get_doc("BOM", po.bom)
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
