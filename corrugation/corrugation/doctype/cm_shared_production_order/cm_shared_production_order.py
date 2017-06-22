# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from corrugation.corrugation.doctype.cm_production_order.cm_production_order import select_rolls_for_box

class CMSharedProductionOrder(Document):
	def get_item_name(self, item_type):
		if len(self.paper_rolls) == 0: return None
		for roll_item in self.paper_rolls:
			if roll_item.rm_type == item_type:
				if (roll_item.paper == None): continue
				print "Trying get the roll {0}".format(roll_item.paper)
				roll = frappe.get_doc("CM Paper Roll", roll_item.paper)
				return roll.paper
		return None

	def is_matching_paper(self, item_info):
		if (len(self.box_details) == 1): return {"Result": True}
		box_details = frappe.get_doc("CM Box Description", item_info["box_desc"])
		for item in box_details.item_papers:
			matching_item = self.get_item_name(item.rm_type)
			if (matching_item == item.rm): return {"Result": True}
		return {"Result": False}

	def populate_rolls(self):
		#Build a new paper item list for combined production
		self.paper_rolls = []
		paper_items = []
		for paper_box in self.box_details:
			box_details = frappe.get_doc("CM Box Description", paper_box.box_desc)
			for paper_item in box_details.item_papers:
				new_item = None
				for pi in paper_items:
					if pi.rm_type == paper_item.rm_type:
						new_item = pi
						break
				if (new_item == None):
					new_item = frappe.new_doc("CM Paper Item")
					new_item.rm_type = paper_item.rm_type
					new_item.rm = paper_item.rm
					new_item.rm_weight = paper_item.rm_weight * paper_box.planned_qty
					paper_items += [new_item]
				else:
					new_item.rm_weight += paper_item.rm_weight * paper_box.planned_qty


		#populate_rolls_for_box(self, item_info.box_desc, item_info.planned_qty)
		selected_rolls = select_rolls_for_box(paper_items)
		for roll_item in selected_rolls:
			print("Selected roll " + roll_item.paper)
			self.append("paper_rolls", roll_item)

	def get_paper_weights(self, paper_type):
		planned_weight = prod_weight = 0
		for roll_item in self.paper_rolls:
			if roll_item.rm_type == paper_type:
				planned_weight += (roll_item.start_weight - roll_item.est_final_weight)
				prod_weight += (roll_item.start_weight - roll_item.final_weight)
		return (planned_weight, prod_weight)

	def get_planned_paper_ratio(self, box, paper_type):
		box_descr = frappe.get_doc("CM Box Description", paper_box.box)
		total_planned_weight = 0
		for paper_item in box_descr.item_papers:
			if (paper_item.rm_type == paper_type):
				return self.planned_qty * paper_item.rm_weight

	def create_individual_production_orders(self):
		prod_orders = []

		available_rolls = self.paper_rolls
		for paper_box in self.box_details:
			prod_order = frappe.new_doc("CM Production Order")
			prod_order.sales_order = paper_box.sales_order
			prod_order.planned_qty = paper_box.planned_qty
			prod_order.prod_qty = paper_box.prod_qty
			box_descr = frappe.get_doc("CM Box Description", paper_box.box)
			prod_order.bom = box_descr.bom
			prod_order.source_warehouse = self.source_warehouse
			prod_order.target_warehouse = self.target_warehouse

			for paper_item in box_descr.item_papers:
				(planned_weight, prod_weight) = sef.get_paper_weights(paper_box, paper_item.rm_type)
				qty = self.get_planned_paper_quantity(paper_box, paper_item.rm_type)
			for roll in available_rolls:
				new_item = None
				for pi in paper_items:
					if pi.rm_type == paper_item.rm_type:
						new_item = pi
						break
				if (new_item == None):
					new_item = frappe.new_doc("CM Paper Item")
					new_item.rm_type = paper_item.rm_type
					new_item.rm = paper_item.rm
					new_item.rm_weight = paper_item.rm_weight * paper_box.planned_qty
					paper_items += [new_item]
				else:
					new_item.rm_weight += paper_item.rm_weight * paper_box.planned_qty
