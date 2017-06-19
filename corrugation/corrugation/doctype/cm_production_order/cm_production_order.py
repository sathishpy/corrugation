# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.manufacturing.doctype.production_order.production_order import make_stock_entry

class CMProductionOrder(Document):
	def autoname(self):
		self.name = "PO-{0}-{1}".format(self.cm_item, self.sales_order)

	def get_planned_paper_quantity(self, rmtype):
		box_details = frappe.get_doc("CM Box Description", self.cm_box_detail)
		for paper in box_details.item_papers:
			if paper.rm_type == rmtype: return paper.rm_weight * self.cm_planned_qty
		return 0

	def update_box_roll_qty(self):
		added_rolls = []
		for roll_item in self.cm_box_rolls:
			rm_type = roll_item.cm_rm_type
			planned_qty = self.get_planned_paper_quantity(rm_type)
			used_roll = get_prod_used_roll(added_rolls, roll_item.cm_paper, rm_type)
			print ("Amount of {0} paper {1} needed is {2}".format(rm_type, roll_item.cm_paper, planned_qty))
			if used_roll is None:
				roll = frappe.get_doc("CM Paper Roll", roll_item.cm_paper)
				roll_item.cm_start_weight = roll.cm_weight
			else:
				roll_item.cm_start_weight = used_roll.cm_est_final_weight

			if (planned_qty < roll_item.cm_start_weight):
				roll_item.cm_est_final_weight = (roll_item.cm_start_weight - planned_qty)
			else:
				roll_item.cm_est_final_weight = 0
			added_rolls += [roll_item]

	def populate_box_rolls(self):
		box_details = frappe.get_doc("CM Box Description", self.cm_box_detail)
		print ("Got item {0} having bom {1}".format(box_details.name, box_details.item_bom))
		self.cm_bom = box_details.item_bom
		self.cm_box_rolls = []

		available_rolls = []
		#build the unique list
		papers = [pi.rm for pi in box_details.item_papers]
		papers = list(set(papers))

		for paper_name in papers:
			rolls = frappe.get_all("CM Paper Roll", fields={"cm_item" : paper_name})
			available_rolls += rolls
			print("Found {0} rolls for paper {1}".format(len(rolls), paper_name))

		for paper in box_details.item_papers:
			planned_qty = paper.rm_weight * self.cm_planned_qty
			print "{0} Paper {1} needed: {2}".format(paper.rm_type, paper.rm, planned_qty)
			# Select all the rolls needed to manufacture required quantity
			while planned_qty > 0:
				roll = get_prod_used_roll(self.cm_box_rolls, paper.rm, paper.rm_type)
				if roll == None:
					roll = get_smallest_roll(available_rolls, paper.rm)

				if roll is None:
					frappe.throw("Failed to find a roll for {0} paper {1}".format(paper.rm))
					break
				print "Selected Roll is {0} Weight {1}".format(roll.name, roll.cm_weight)

				roll_item = frappe.new_doc("CM Box Roll Detail")
				roll_item.cm_rm_type = paper.rm_type
				roll_item.cm_paper = roll.name
				roll_item.cm_start_weight = roll.cm_weight

				if (roll.cm_weight > planned_qty):
					roll_item.cm_est_final_weight = roll.cm_weight - planned_qty
					planned_qty = 0
				else:
					roll_item.cm_est_final_weight = 0
					planned_qty -= roll.cm_weight

				roll_item.cm_final_weight = roll_item.cm_est_final_weight
				self.append("cm_box_rolls", roll_item)
				print ("Adding {0}".format(roll_item))
				available_rolls = [rl for rl in available_rolls if rl.name != roll.name]

	def get_paper_quantity(self, paper):
		#Prepare a list removing identical rolls
		box_rolls = {}
		for roll_item in self.cm_box_rolls:
			ri = box_rolls.get(roll_item.cm_paper)
			if (ri == None):
				box_rolls[roll_item.cm_paper] = roll_item
			else:
				if (roll_item.cm_final_weight > ri.cm_final_weight):
					ri.cm_start_weight = roll_item.cm_start_weight
					box_rolls[ri.cm_paper] = ri
				else:
					box_rolls[ri.cm_paper] = roll_item
					roll_item.cm_start_weight = ri.cm_start_weight

		qty = 0
		for (key, roll_item) in box_rolls.items():
			roll = frappe.get_doc("CM Paper Roll", roll_item.cm_paper)
			if roll.cm_item != paper: continue
			qty += (roll_item.cm_start_weight - roll_item.cm_final_weight)
			print("Weight of roll {0} is {1}".format(roll_item.cm_paper, qty))
		return qty

	def get_all_order_items(self):
		items = frappe.db.sql("""select item_code, qty from `tabSales Order Item`
								where parent='{0}'""".format(self.sales_order), as_dict=1);
		return items

@frappe.whitelist()
def is_paper_item(rm):
	if "paper" in rm.item_name or "Paper" in rm.item_name:
		return True
	return False

def get_prod_used_roll(rolls, paper, rm_type):
	reuse_roll = None
	for p_roll in rolls:
		roll = frappe.get_doc("CM Paper Roll", p_roll.cm_paper)
		if roll.cm_item != paper: continue
		#Flute and bottom paper used simultaneosuly, so can't be shared
		sharing_conflict = False
		if (p_roll.cm_rm_type == "Flute" and rm_type == "Bottom"): sharing_conflict = True
		if (p_roll.cm_rm_type == "Bottom" and rm_type == "Flute"): sharing_conflict = True
		if (p_roll.cm_rm_type == "Flute Liner" and rm_type == "Liner"): sharing_conflict = True
		if (p_roll.cm_rm_type == "Liner" and rm_type == "Flute Liner"): sharing_conflict = True
		# Handle duplicate entries of shared rolls
		if (sharing_conflict):
			if (reuse_roll != None and reuse_roll.name == roll.name):
				reuse_roll = None
			continue

		print("Found roll {0} of weight {1} for {2}".format(p_roll.cm_paper, p_roll.cm_est_final_weight, rm_type))
		if (reuse_roll != None and reuse_roll.name == roll.name):
			if p_roll.cm_est_final_weight < 10:
				reuse_roll = None
				continue
		if p_roll.cm_est_final_weight > 10:
			reuse_roll = roll
			reuse_roll.cm_weight = p_roll.cm_est_final_weight
	# Update the weight, but don't save it
	return reuse_roll

def get_smallest_roll(rolls, paper):
	weight = 100000
	small_roll = None
	for p_roll in rolls:
		roll = frappe.get_doc("CM Paper Roll", p_roll.name)
		if (roll.cm_status == "Ready" and roll.cm_item == paper and roll.cm_weight < weight and roll.cm_weight > 10):
			small_roll = roll
			weight = roll.cm_weight
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

@frappe.whitelist()
def make_new_pe(source_name):
	cm_po = frappe.get_doc("CM Production Order", source_name)
	print("Creating PO for CM Order {0}".format(cm_po.name))

	orders = frappe.get_all("Production Order", fields={"production_item":cm_po.cm_item, "sales_order":cm_po.sales_order})
	po = None
	if len(orders) > 0: po = orders[0]
	if po is None:
		po = frappe.new_doc("Production Order")
		po.production_item = cm_po.cm_item
		po.bom_no = cm_po.cm_bom
		po.sales_order = cm_po.sales_order
		po.skip_transfer = True
		po.qty = cm_po.cm_box_qty
		po.wip_warehouse = po.source_warehouse = cm_po.cm_source_wh
		po.fg_warehouse = cm_po.cm_target_wh
		po.submit()

	stock_entry = make_stock_entry(po.name, "Manufacture", po.qty)
	se = frappe.new_doc("Stock Entry")
	se.update(stock_entry)

	update_paper_quantity(cm_po, se)
	se.calculate_rate_and_amount()

	for roll_item in cm_po.cm_box_rolls:
		roll = frappe.get_doc("CM Paper Roll", roll_item.cm_paper)
		roll.status = "Ready"
		roll.cm_weight = roll_item.cm_final_weight
		roll.save()

	return se.as_dict()
