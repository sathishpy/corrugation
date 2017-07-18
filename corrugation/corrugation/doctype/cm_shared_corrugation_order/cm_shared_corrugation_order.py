# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from corrugation.corrugation.roll_selection import select_rolls_for_box
from corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order import update_roll_qty
from corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order import set_new_layer_defaults

import copy

class CMSharedCorrugationOrder(Document):
	def get_item_name(self, item_type):
		if len(self.paper_rolls) == 0: return None
		for roll_item in self.paper_rolls:
			if roll_item.rm_type == item_type:
				if (roll_item.paper_roll == None): continue
				print "Trying get the roll {0}".format(roll_item.paper_roll)
				roll = frappe.get_doc("CM Paper Roll", roll_item.paper_roll)
				return roll.paper
		return None

	def is_compatible_bom(self):
		count = len(self.box_details)
		if (count == 1): return {"Result": True}

		for box in self.box_details:
			box_desc = frappe.get_doc("CM Box Description", box.box_desc)
			for item in box_desc.item_papers:
				matching_item = self.get_item_name(item.rm_type)
				if (matching_item != item.rm): return {"Result": False}
		return {"Result": True}

	def populate_order_items(self, item_info):
		if "sales_order" not in item_info: return

		order_items = frappe.db.sql("""select item_code, qty from `tabSales Order Item`
								where parent='{0}'""".format(item_info["sales_order"]), as_dict=1);
		box_item = next((bi for bi in self.box_details if bi.sales_order == item_info["sales_order"]), None)
		print("Sales order {0} matches row {1}".format(item_info["sales_order"], box_item.sales_order))
		if (len(order_items) > 0 and box_item is not None):
			selected_item = order_items[0]
			box_item.box = selected_item.item_code
			box_item.mfg_qty = selected_item.qty
			box_boms = frappe.get_all("CM Box Description", filters={'box': box_item.box})
			box_item.box_desc = box_boms[0].name

	def populate_rolls(self):
		self.paper_rolls = []
		if (self.manual_entry): return

		paper_items = []
		for paper_box in self.box_details:
			box_details = frappe.get_doc("CM Box Description", paper_box.box_desc)
			for paper_item in box_details.item_papers:
				if ("Top" in self.layer_type and paper_item.rm_type != "Top"): continue
				if ("Flute" in self.layer_type and paper_item.rm_type == "Top"): continue
				new_item = next((pi for pi in paper_items if pi.rm_type == paper_item.rm_type and pi.rm == paper_item.rm), None)
				if (new_item == None):
					new_item = frappe.new_doc("CM Paper Item")
					new_item.rm_type = paper_item.rm_type
					new_item.rm = paper_item.rm
					new_item.rm_weight = paper_item.rm_weight * paper_box.mfg_qty
					paper_items += [new_item]
				else:
					new_item.rm_weight += paper_item.rm_weight * paper_box.mfg_qty

		#populate_rolls_for_box(self, item_info.box_desc, item_info.mfg_qty)
		selected_rolls = select_rolls_for_box(paper_items)
		for roll_item in selected_rolls:
			print("Selected roll " + roll_item.paper_roll)
			self.append("paper_rolls", roll_item)

	def update_box_roll_qty(self):
		update_roll_qty(self)

	def set_new_layer_defaults(self):
		set_new_layer_defaults(self, self.layer_type)

	def create_used_paper_weight_map(self):
		weight_map = {}
		# Find the total paper use dfor each layer
		total_paper_used = {"Top": 0, "Flute": 0, "Liner": 0}
		for paper_roll in self.paper_rolls:
			total_paper_used[paper_roll.rm_type] += (paper_roll.start_weight - paper_roll.final_weight)

		# Find the planned paper weight of each layer for each box
		planned_total_paper_weight = {"Top": 0, "Flute": 0, "Liner": 0}
		for cbbox in self.box_details:
			box_desc = frappe.get_doc("CM Box Description", cbbox.box_desc)
			for paper_item in box_desc.item_papers:
				planned_total_paper_weight[paper_item.rm_type] += (paper_item.rm_weight * cbbox.mfg_qty)

		for cbbox in self.box_details:
			box_desc = frappe.get_doc("CM Box Description", cbbox.box_desc)
			actual_paper_used = {"Top": 0, "Flute": 0, "Liner": 0}
			for paper_item in box_desc.item_papers:
				paper_weight_ratio = float((paper_item.rm_weight * cbbox.mfg_qty)/planned_total_paper_weight[paper_item.rm_type])
				actual_paper_used[paper_item.rm_type] = paper_weight_ratio * total_paper_used[paper_item.rm_type]
				print("Box:{0}     Type:{1}   Ratio:{2}".format(cbbox.box, paper_item.rm_type, paper_weight_ratio))
			weight_map[cbbox.box] = actual_paper_used

		return weight_map


	def create_individual_production_orders(self):
		weight_map = self.create_used_paper_weight_map()
		print ("Box          Top         Flute     Liner")
		for key, value in weight_map.items():
			weights = ""
			for ptype, weight in value.items():
				weights += str(weight) + "     "
			print ("{0}  {1}".format(key, weights))

		#Build a new paper item list for combined production
		available_rolls = copy.deepcopy(self.paper_rolls)
		for roll in available_rolls:
			roll.final_weight = roll.start_weight

		for paper_box in self.box_details:
			weights = weight_map[paper_box.box]
			crg_order = frappe.new_doc("CM Corrugation Order")
			crg_order.sales_order = paper_box.sales_order
			crg_order.box = paper_box.box
			crg_order.box_desc = paper_box.box_desc
			crg_order.mfg_qty = paper_box.mfg_qty
			crg_order.layer_type = self.layer_type

			box_desc = frappe.get_doc("CM Box Description", paper_box.box_desc)
			crg_order.bom = box_desc.item_bom

			for ptype, weight in weights.items():
				while weight > 0:
					roll = next((rl for rl in available_rolls if rl.rm_type == ptype and rl.start_weight > 0), None)
					if (roll.start_weight - weight) > 0:
						roll.final_weight = roll.start_weight - weight
						weight = 0
					else:
						roll.final_weight = 0
						weight = weight - roll.start_weight
					planned_weight = next((rm.rm_weight for rm in box_desc.item_papers if rm.rm_type == ptype), None)
					roll.est_final_weight = roll.start_weight - (planned_weight * paper_box.mfg_qty)
					crg_order.append("paper_rolls", copy.copy(roll))
					roll.start_weight = roll.final_weight

			crg_order.submit()

		for roll in available_rolls:
			print("Roll {0} start={1} Final={2}".format(roll.paper_roll, roll.start_weight, roll.final_weight))

	def before_submit(self):
		self.create_individual_corrugation_orders()
