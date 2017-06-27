# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.manufacturing.doctype.production_order.production_order import make_stock_entry

class CMProductionOrder(Document):
	def autoname(self):
		self.name = "PO-{0}-{1}".format(self.box, self.sales_order)

	def get_planned_paper_quantity(self, rmtype):
		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		for paper in box_details.item_papers:
			if paper.rm_type == rmtype: return paper.rm_weight * self.planned_qty
		return 0

	def update_box_roll_qty(self):
		added_rolls = []
		for roll_item in self.paper_rolls:
			rm_type = roll_item.rm_type
			planned_qty = self.get_planned_paper_quantity(rm_type)
			used_roll = get_prod_used_roll(added_rolls, roll_item.paper_roll, rm_type)
			print ("Amount of {0} paper {1} needed is {2}".format(rm_type, roll_item.paper, planned_qty))
			if used_roll is None:
				roll = frappe.get_doc("CM Paper Roll", roll_item.paper)
				roll_item.start_weight = roll.weight
			else:
				roll_item.start_weight = used_roll.est_final_weight

			if (planned_qty < roll_item.start_weight):
				roll_item.est_final_weight = (roll_item.start_weight - planned_qty)
			else:
				roll_item.est_final_weight = 0
			added_rolls += [roll_item]

	def populate_box_rolls(self):
		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		print ("Manufacture {0} items {1} having bom {2}".format(self.planned_qty, box_details.name, box_details.item_bom))
		self.bom = box_details.item_bom
		self.paper_rolls = []
		#Build a new paper item list for this production
		paper_items = []
		for paper_item in box_details.item_papers:
			new_item = frappe.new_doc("CM Paper Item")
			new_item.rm_type = paper_item.rm_type
			new_item.rm = paper_item.rm
			new_item.rm_weight = float(paper_item.rm_weight * self.planned_qty)
			paper_items += [new_item]

		selected_rolls = select_rolls_for_box(paper_items)
		for roll_item in selected_rolls:
			self.append("paper_rolls", roll_item)

	def get_paper_quantity(self, paper):
		#Prepare a list removing identical rolls
		box_rolls = {}
		for roll_item in self.paper_rolls:
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

	def get_all_order_items(self):
		items = frappe.db.sql("""select item_code, qty from `tabSales Order Item`
								where parent='{0}'""".format(self.sales_order), as_dict=1);
		return items

	def on_submit(self):
		check_material_availability(self)
		submit_production_order(self)
		create_new_stock_entry(self)

@frappe.whitelist()
def select_rolls_for_box(paper_items):
	added_rolls = []
	available_rolls = []
	#build the unique list
	papers = [pi.rm for pi in paper_items]
	papers = list(set(papers))

	for paper_name in papers:
		rolls = frappe.get_all("CM Paper Roll", fields={"paper" : paper_name})
		available_rolls += rolls
		print("Found {0} rolls for paper {1}".format(len(rolls), paper_name))

	for paper in paper_items:
		planned_qty = paper.rm_weight
		print "{0} Paper {1} needed: {2}".format(paper.rm_type, paper.rm, planned_qty)
		# Select all the rolls needed to manufacture required quantity
		while planned_qty > 0:
			roll = get_prod_used_roll(added_rolls, paper.rm, paper.rm_type)
			if roll == None:
				roll = get_smallest_roll(available_rolls, paper.rm)

			if roll is None:
				frappe.throw("Failed to find a roll for {0} paper {1}".format(paper.rm))
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
			print ("Adding {0}".format(roll_item))
			available_rolls = [rl for rl in available_rolls if rl.name != roll.name]
	return added_rolls

@frappe.whitelist()
def is_paper_item(rm):
	if "paper" in rm.item_name or "Paper" in rm.item_name:
		return True
	return False

def get_prod_used_roll(rolls, paper, rm_type):
	reuse_roll = None
	for p_roll in rolls:
		roll = frappe.get_doc("CM Paper Roll", p_roll.paper_roll)
		if roll.paper != paper: continue
		#Flute and bottom paper used simultaneosuly, so can't be shared
		sharing_conflict = False
		if (p_roll.rm_type == "Flute" and rm_type == "Bottom"): sharing_conflict = True
		if (p_roll.rm_type == "Bottom" and rm_type == "Flute"): sharing_conflict = True
		if (p_roll.rm_type == "Flute Liner" and rm_type == "Liner"): sharing_conflict = True
		if (p_roll.rm_type == "Liner" and rm_type == "Flute Liner"): sharing_conflict = True
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

def get_smallest_roll(rolls, paper):
	weight = 100000
	small_roll = None
	for p_roll in rolls:
		roll = frappe.get_doc("CM Paper Roll", p_roll.name)
		if (roll.status == "Ready" and roll.paper == paper and roll.weight < weight and roll.weight > 10):
			small_roll = roll
			weight = roll.weight
	return small_roll

def update_paper_quantity(po, se):
	for item in se.items:
		print ("Updating item {0}".format(item.item_code))
		rm = frappe.get_doc("Item", item.item_code)
		if not is_paper_item(rm): continue
		qty = po.get_paper_quantity(rm.name)
		if qty != 0:
			print("Updating item {0} qunatity to {1}".format(rm.name, qty))
			item.qty = qty
	return se

def submit_production_order(cm_po):
	orders = frappe.get_all("Production Order", fields={"production_item":cm_po.box, "sales_order":cm_po.sales_order})
	if len(orders) > 0:
		print("Production order {0} is already created".format(orders[0].name))
		return

	po = frappe.new_doc("Production Order")
	po.production_item = cm_po.box
	po.bom_no = cm_po.bom
	po.sales_order = cm_po.sales_order
	po.skip_transfer = True
	po.qty = cm_po.prod_qty
	po.wip_warehouse = po.source_warehouse = cm_po.source_warehouse
	po.fg_warehouse = cm_po.target_warehouse
	po.submit()

def update_production_roll_qty(cm_po):
	for roll_item in cm_po.paper_rolls:
		roll = frappe.get_doc("CM Paper Roll", roll_item.paper_roll)
		roll.status = "Ready"
		roll.weight = roll_item.final_weight
		roll.save()

@frappe.whitelist()
def create_new_stock_entry(cm_po):
	orders = frappe.get_all("Production Order", fields={"production_item":cm_po.box, "sales_order":cm_po.sales_order})
	if len(orders) > 0: po = orders[0]
	else: frappe.throw("Unable to find the production order for sales_order {0}".format(cm_po.sales_order))

	stock_entry = make_stock_entry(po.name, "Manufacture", po.qty)
	se = frappe.new_doc("Stock Entry")
	se.update(stock_entry)

	update_paper_quantity(cm_po, se)
	se.calculate_rate_and_amount()
	se.submit()

	update_production_roll_qty(cm_po)

@frappe.whitelist()
def check_material_availability(cm_po):
	#try to use the stock_entry functionality
	pass

@frappe.whitelist()
def make_new_stock_entry(source_name):
	cm_po = frappe.get_doc("CM Production Order", source_name)
	print("Creating PO for CM Order {0}".format(cm_po.name))

	se = create_stock_entry(cm_po)

	return se.as_dict()
