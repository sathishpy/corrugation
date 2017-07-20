# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from corrugation.corrugation.roll_selection import select_rolls_for_box
from corrugation.corrugation.doctype.cm_box_description.cm_box_description import get_planned_paper_quantity
from corrugation.corrugation.doctype.cm_box_description.cm_box_description import get_no_of_boards_for_box
from corrugation.corrugation.doctype.cm_box_description.cm_box_description import get_no_of_boxes_from_board
from frappe import _
import copy

class CMCorrugationOrder(Document):
	def autoname(self):
		items = frappe.db.sql_list("""select name from `tabCM Corrugation Order`
										where box='{0}' and layer_type='{1}'""".format(self.box, self.layer_type))
		if items: idx = len(items) + 1
		else: idx = 1
		self.name = "Crg-" + self.layer_type + "-" + self.box + ('-%.3i' % idx)

	def populate_order_items(self):
		if (self.sales_order is None): return
		order_items = frappe.db.sql("""select item_code, qty from `tabSales Order Item`
										where parent='{0}'""".format(self.sales_order), as_dict=1);
		if (len(order_items) > 0):
			selected_item = order_items[0]
			self.box = selected_item.item_code
			self.order_qty = selected_item.qty
			box_boms = frappe.get_all("CM Box Description", filters={'box': self.box})
			self.box_desc = box_boms[0].name
			self.update_board_count()
		return order_items

	def update_board_count(self):
		self.mfg_qty = get_no_of_boards_for_box(self.box_desc, self.layer_type, self.order_qty)

	def update_layer(self):
		self.update_board_count()
		self.populate_rolls()

	def populate_rolls(self):
		paper_items, self.paper_rolls = [], []
		if (self.manual_entry): return

		box_count = get_no_of_boxes_from_board(self.box_desc, self.layer_type, self.mfg_qty)
		print("Getting {0} paper for {1} boxes".format(self.layer_type, box_count))
		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		for paper_item in box_details.item_papers:
			if ("Top" in self.layer_type and paper_item.rm_type != "Top"): continue
			if ("Flute" in self.layer_type and paper_item.rm_type == "Top"): continue
			new_item = next((item for item in paper_items if item.rm == paper_item.rm and item.rm_type == paper_item.rm_type), None)
			if (new_item != None):
				new_item.rm_weight += float(paper_item.rm_weight * box_count)
				continue
			new_item = frappe.new_doc("CM Paper Item")
			new_item.rm_type = paper_item.rm_type
			new_item.rm = paper_item.rm
			new_item.rm_weight = float(paper_item.rm_weight * box_count)
			paper_items += [new_item]

		selected_rolls = select_rolls_for_box(paper_items)
		for roll_item in selected_rolls:
			print("Selected roll " + roll_item.paper_roll)
			self.append("paper_rolls", roll_item)

		self.board_name = box_details.get_board_name(self.get_layer_number())

	def update_box_roll_qty(self):
		update_roll_qty(self)

	def set_new_layer_defaults(self):
		set_new_layer_defaults(self, self.layer_type)

	def get_layer_number(self):
		roll_item = next((roll_item for roll_item in self.paper_rolls if roll_item.rm_type != "Flute"), None)
		roll = frappe.get_doc("CM Paper Roll", roll_item.paper_roll)
		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		layer = 1
		for paper_item in box_details.item_papers:
			if (paper_item.rm_type == roll_item.rm_type and roll.paper == paper_item.rm): return layer
			layer += 1
		frappe.throw("Failed to find the layer number")

	def get_planned_paper_qty(self, rm_type, paper):
		return get_planned_paper_quantity(self.box_desc, rm_type, paper, self.mfg_qty)

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
		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		board_item.qty = self.mfg_qty
		board_item.t_warehouse = frappe.db.get_value("Warehouse", filters={"warehouse_name": _("Stores")})
		se.append("items", board_item)
		se.calculate_rate_and_amount()
		se.submit()

@frappe.whitelist()
def get_used_paper_qunatity_from_rolls(paper_rolls, paper):
	box_rolls = {}
	for roll_item in paper_rolls:
		ri = box_rolls.get(roll_item.paper_roll)
		if (ri == None):
			box_rolls[roll_item.paper_roll] = copy.deepcopy(roll_item)
		else:
			if (ri.final_weight > roll_item.final_weight):
				ri.final_weight = roll_item.final_weight
			else:
				ri.start_weight = roll_item.start_weight

	qty = 0
	for (key, roll_item) in box_rolls.items():
		roll = frappe.get_doc("CM Paper Roll", roll_item.paper_roll)
		if roll.paper != paper: continue
		qty += (roll_item.start_weight - roll_item.final_weight)
		print("Weight of roll {0} is {1}".format(roll_item.paper_roll, qty))
	return qty

@frappe.whitelist()
def get_matching_last_used_roll(rolls, matching_roll, rm_type):
	idx = len(rolls)
	potential_conflict = True
	paper = frappe.get_doc("CM Paper Roll", matching_roll).paper
	while idx > 0:
		idx = idx - 1
		roll = frappe.get_doc("CM Paper Roll", rolls[idx].paper_roll)
		if roll.paper != paper: continue
		if (potential_conflict and rolls[idx].paper_roll == matching_roll and rolls[idx].rm_type == "Flute" and rm_type == "Liner"):
			potential_conflict = False
			frappe.throw("Cannot use same roll for flute and liner")
			continue
		return rolls[idx]

@frappe.whitelist()
def update_roll_qty(co):
	planned_qty, added_rolls = {"Top": -1, "Flute": -1, "Liner": -1}, []
	for roll_item in co.paper_rolls:
		roll, rm_type = frappe.get_doc("CM Paper Roll", roll_item.paper_roll), roll_item.rm_type
		roll_item.start_weight = roll.weight
		if (planned_qty[rm_type] == -1):
			planned_qty[rm_type] = co.get_planned_paper_qty(rm_type, roll.paper)
		print ("Amount of {0} paper {1} needed is {2}".format(rm_type, roll.paper, planned_qty[rm_type]))
		used_roll = get_matching_last_used_roll(added_rolls, roll_item.paper_roll, rm_type)
		if used_roll is not None:
			print "Used roll is {0} having final weight {1}".format(used_roll.paper_roll, used_roll.final_weight)
			if used_roll.est_final_weight < 0:
				used_roll.est_final_weight = 0
			elif used_roll.paper_roll == roll_item.paper_roll:
				roll_item.start_weight = used_roll.final_weight

		roll_item.est_final_weight = (roll_item.start_weight - planned_qty[rm_type])
		if (roll_item.final_weight == -1): roll_item.final_weight = max(0, roll_item.est_final_weight)
		planned_qty[rm_type] = planned_qty[rm_type] - roll_item.start_weight + roll_item.final_weight
		added_rolls += [roll_item]

@frappe.whitelist()
def update_production_roll_qty(cm_po):
	for roll_item in cm_po.paper_rolls:
		roll = frappe.get_doc("CM Paper Roll", roll_item.paper_roll)
		roll.status = "Ready"
		roll.weight = roll_item.final_weight
		roll.save()

@frappe.whitelist()
def get_next_layer(layer):
	layers = ["Top", "Flute", "Liner", "Flute"]
	for idx in range(0, len(layers)):
		if (layer == layers[idx]):
			return layers[idx + 1]

@frappe.whitelist()
def set_new_layer_defaults(prod_order, first_layer):
	rolls_count, layer = len(prod_order.paper_rolls), first_layer
	last_row = prod_order.paper_rolls[rolls_count-1]
	previous_roll = None
	if (rolls_count > 1): previous_roll = prod_order.paper_rolls[rolls_count-2]
	if (previous_roll != None):
		layer = previous_roll.rm_type
		if (previous_roll.est_final_weight > 0):
			layer = get_next_layer(layer)
	last_row.rm_type = layer
	last_row.final_weight = -1

@frappe.whitelist()
def make_other_layer(source_name):
	crg_order = frappe.get_doc("CM Corrugation Order", source_name)
	other_order = frappe.new_doc("CM Corrugation Order")
	other_order.sales_order = crg_order.sales_order
	other_order.layer_type = "Flute"
	if (crg_order.layer_type == "Flute"):
		other_order.layer_type = "Top"
	other_order.populate_order_items()
	other_order.populate_rolls()
	return other_order.as_dict()

@frappe.whitelist()
def filter_rolls(doctype, txt, searchfield, start, page_len, filters):
	box_desc = frappe.get_doc("CM Box Description", filters["box_desc"])
	layer_type = filters["layer_type"]
	ignore_bom = filters["ignore_bom"]

	paper_filter = ""
	papers = ["'" + paper_item.rm + "'" for paper_item in box_desc.item_papers if paper_item.rm_type == layer_type]
	if not ignore_bom:
		paper_filter = "and roll.paper in ({0})".format(",".join(paper for paper in papers))

	filter_query =	"""select roll.name, roll.weight
	 					from `tabCM Paper Roll` roll
						where roll.weight > 10
							{0}
							and roll.name LIKE %(txt)s
						order by roll.weight * 1 asc
					""".format(paper_filter)
	#print "Searching rolls matching paper {0} with query {1}".format(",".join(paper for paper in papers), filter_query)
	return frappe.db.sql(filter_query, {"txt": "%%%s%%" % txt})
