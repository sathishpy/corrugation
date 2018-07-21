# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.manufacturing.doctype.production_order.production_order import make_stock_entry
<<<<<<< HEAD
from erpnext.stock.utils import get_latest_stock_qty
from corrugation.corrugation.roll_selection import select_rolls_for_box
from corrugation.corrugation.utils import delete_submitted_document
from corrugation.corrugation.doctype.cm_box_description.cm_box_description import get_planned_paper_quantity
from corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order import update_production_roll_qty
from corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order import cancel_production_roll_qty
from corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order import update_roll_qty
from corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order import get_used_paper_qunatity_from_rolls
from corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order import set_new_layer_defaults
from datetime import datetime
from datetime import timedelta

class CMProductionOrder(Document):
	def autoname(self):
		orders = frappe.db.sql_list("""select name from `tabCM Production Order` where box='{0}'""".format(self.box))
		self.name = "PO-{0}-{1}".format(self.box, len(orders))

	def populate_order_items(self):
		if (self.sales_order is None): return
		order_items = frappe.db.sql("""select item_code, qty from `tabSales Order Item`
										where parent='{0}'""".format(self.sales_order), as_dict=1);

		for idx in range(0, len(order_items)):
			self.box = order_items[idx].item_code
			self.mfg_qty = self.order_qty = order_items[idx].qty
			self.stock_qty = get_latest_stock_qty(self.box)
			if (self.stock_qty is None or self.stock_qty == 0): break
		self.populate_item_prod_info()

	def populate_item_prod_info(self):
		if (not self.box): return
		self.stock_qty = get_latest_stock_qty(self.box)
		box_boms = frappe.get_all("CM Box Description", filters={'box': self.box})
		self.box_desc = box_boms[0].name

	def update_box_roll_qty(self):
		if (self.box_desc is None): return
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
		if (self.manual_entry): return

		self.paper_rolls = []
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
=======

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
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
			paper_items += [new_item]

		selected_rolls = select_rolls_for_box(paper_items)
		for roll_item in selected_rolls:
<<<<<<< HEAD
			print ("Adding roll {0} as {1}".format(roll_item.paper_roll, roll_item.rm_type))
			self.append("paper_rolls", roll_item)

	def populate_box_boards(self):
		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		for board in set(box_details.get_all_boards()):
			layer_type = "Top" if "Top" in board else "Flute"
			no_of_board_layers = 1 if "Top" in board else int(int(box_details.item_ply_count)/2)
			needed_boards = (self.mfg_qty/box_details.get_items_per_board()) * no_of_board_layers
			filters= {"box_desc": box_details.name, "layer_type": layer_type, "ignore_bom": 0}
			boards = get_filtered_boards("", filters)
			if (len(boards) == 0): continue
			bom_board_idx = next((idx for idx in range(0, len(boards)) if boards[idx][0] == board), 0)
			idx = 0
			boards[idx], boards[bom_board_idx] = boards[bom_board_idx], boards[idx]
			while needed_boards > 0 and idx < len(boards):
				(board_name, qty) = boards[idx]
				print "Adding {0} board items for {1}".format(needed_boards, board_name)
				new_item = frappe.new_doc("CM Production Board Detail")
				new_item.layer_type = layer_type
				new_item.layer = board_name
				new_item.stock_qty = qty
				new_item.used_qty = min(new_item.stock_qty, needed_boards)
				self.append("paper_boards", new_item)
				needed_boards -= new_item.used_qty
				idx += 1

	def update_board_qty(self):
		for board in self.paper_boards:
			if (board.layer is None): continue
			board.stock_qty = get_latest_stock_qty(board.layer)

	def set_new_layer_defaults(self):
		set_new_layer_defaults(self, "Top")

	def replace_paper_with_boards(self, se):
		other_items = [item for item in se.items if "PPR" not in item.item_code]
		se.items = []
		for board in self.paper_boards:
			board_item = frappe.new_doc("Stock Entry Detail")
			board_item.item_code = board.layer
			board_item.qty = board.used_qty
			board_item.s_warehouse = frappe.db.get_single_value("Manufacturing Settings", "default_wip_warehouse")
			se.append("items", board_item)

		for item in other_items:
			print ("Re-adding item {0}".format(item.item_code))
			se.append("items", item)

	def update_paper_quantity(self, se):
		if (self.use_boards):
			return self.replace_paper_with_boards(se)

		for item in se.items:
			rm = frappe.get_doc("Item", item.item_code)
			if rm.item_group != "Paper": continue
			print ("Updating item {0}".format(item.item_code))
			qty = get_used_paper_qunatity_from_rolls(self.paper_rolls, rm.name)
			if qty != 0:
				print("Updating item {0} qunatity to {1}".format(rm.name, qty))
				item.qty = qty
		return se

	def update_rm_quantity(self, se):
		box_details = frappe.get_doc("CM Box Description", self.box_desc)
		for item in se.items:
			if (frappe.db.get_value("Item", item.item_code, "item_group") == "Paper"): continue
			bom = frappe.get_doc("BOM", box_details.item_bom)
			bom_item = next((bi for bi in bom.items if bi.item_code == item.item_code), None)
			if (bom_item == None): continue
			print ("Updating RM {0} for quantity {1}".format(item.item_code, self.mfg_qty))
			qty = bom_item.qty * self.mfg_qty
			if qty != 0:
				print("Updating item {0} qunatity to {1}".format(item.item_code, qty))
				item.qty = qty
		return se

	def get_planned_paper_qty(self, rm_type, paper):
		return get_planned_paper_quantity(self.box_desc, rm_type, paper, self.mfg_qty)

	def update_production_cost(self):
		self.act_rm_cost = 0
		self.crg_orders = []
		for board_item in self.paper_boards:
			corr_orders = frappe.db.sql("""select name from `tabCM Corrugation Order`
											where board_name='{0}' and stock_batch_qty > 0 and docstatus != 2""".format(board_item.layer), as_dict=1)
			print("Corrugation orders for layer {0} are {1}".format(board_item.layer, len(corr_orders)))
			needed_qty = board_item.used_qty
			board_cost = 0
			for crg_order in corr_orders:
				order = frappe.get_doc("CM Corrugation Order", crg_order.name)
				remaining_in_order = max(0, order.stock_batch_qty - needed_qty)
				used_qty = order.stock_batch_qty - remaining_in_order
				needed_qty = needed_qty - used_qty

				order_item = frappe.new_doc("CM Corrugation Board Item")
				order_item.crg_order = crg_order.name
				order_item.crg_date = order.mfg_date
				order_item.board_count = used_qty
				self.append("crg_orders", order_item)
				board_cost += used_qty * order.get_paper_cost_per_board()
				print("Cost of {0} boards {1} is {2}".format(used_qty, board_item.layer, board_cost))
			 	if needed_qty <= 0:
					break
			self.act_rm_cost += (board_cost/self.mfg_qty)
		self.act_rm_cost += frappe.db.get_value("CM Box Description", self.box_desc, "item_misc_cost")
		profit = frappe.db.get_value("CM Box Description", self.box_desc, "item_profit_amount")
		self.profit = profit + self.planned_rm_cost - self.act_rm_cost

	def get_used_paper_qty(self):
		paper_qty = 0
		for order_item in self.crg_orders:
			order = frappe.get_doc("CM Corrugation Order", order_item.crg_order)
			paper_qty += order_item.board_count * order.get_paper_qty_per_board()
		return paper_qty

	def update_production_cost_after_submit(self):
		board_cost = 0
		for order_item in self.crg_orders:
			order = frappe.get_doc("CM Corrugation Order", order_item.crg_order)
			board_cost += order_item.board_count * order.get_paper_cost_per_board()
		self.act_rm_cost = (board_cost/self.mfg_qty)
		self.act_rm_cost += frappe.db.get_value("CM Box Description", self.box_desc, "item_misc_cost")
		profit = frappe.db.get_value("CM Box Description", self.box_desc, "item_profit_amount")
		self.profit = profit + self.planned_rm_cost - self.act_rm_cost

	def validate_used_corrugated_boards(self):
		used_board_count = 0
		for board_item in self.paper_boards:
			used_board_count += board_item.used_qty

		tracked_board_count = 0
		for crg_order in self.crg_orders:
			tracked_board_count += crg_order.board_count

		if (used_board_count != tracked_board_count):
			frappe.throw("Not all used boards in production order have been tracked to corrugation order")

	def update_used_corrugated_boards(self):
		for crg_order in self.crg_orders:
			order = frappe.get_doc("CM Corrugation Order", crg_order.crg_order)
			order.stock_batch_qty = order.stock_batch_qty - crg_order.board_count
			order.save()

	def revert_used_corrugated_boards(self):
		for crg_order in self.crg_orders:
			order = frappe.get_doc("CM Corrugation Order", crg_order.crg_order)
			order.stock_batch_qty = order.stock_batch_qty + crg_order.board_count
			order.save()

	def validate(self):
		if (self.box not in self.name):
			frappe.throw("Rename(Menu->Rename) the document with {0} as box was updated".format(self.box))

	def on_update(self):
		check_material_availability(self)
		self.planned_rm_cost = frappe.db.get_value("CM Box Description", self.box_desc, "item_paper_cost")
		self.planned_rm_cost += frappe.db.get_value("CM Box Description", self.box_desc, "item_misc_cost")
		self.update_production_cost()

	def before_submit(self):
		submit_sales_order(self.sales_order)
		self.validate_used_corrugated_boards()
		self.prod_order = submit_production_order(self)
		self.stock_entry = create_new_stock_entry(self)
		update_production_roll_qty(self)
		self.update_used_corrugated_boards()

	def delete_stock_and_production_entry(self, stock_entry, prod_order):
		delete_submitted_document("Stock Entry", stock_entry)
		delete_submitted_document("Production Order", prod_order)
		self.stock_entry = self.prod_order = None

	def on_cancel(self):
		self.delete_stock_and_production_entry(self.stock_entry, self.prod_order)
		cancel_production_roll_qty(self)
		self.revert_used_corrugated_boards()

	def update_production_quantity(self, qty):
		stock_difference = qty - self.mfg_qty
		self.mfg_qty = qty
		self.update_production_cost_after_submit()
		self.create_difference_stock_entry(stock_difference)
		print("Updating produced quantity from {0} to {1}".format(self.mfg_qty, qty))
		self.save(ignore_permissions=True)

	def create_difference_stock_entry(self, quantity):
		se = frappe.new_doc("Stock Entry")
		se.purpose = "Repack"
		se.from_bom = 0
		se.to_warehouse  = frappe.db.get_single_value("Manufacturing Settings", "default_fg_warehouse")
		box_item = frappe.new_doc("Stock Entry Detail")
		box_item.item_code = self.box
		se.fg_completed_qty = box_item.qty = quantity
		se.set_posting_time = True
		nextday = datetime.strptime(self.mfg_date, "%Y-%m-%d") + timedelta(days=1)
		se.posting_date = datetime.strftime(nextday, "%Y-%m-%d")
		se.append("items", box_item)
		se.calculate_rate_and_amount()
		se.submit()

def submit_production_order(cm_po):
	po = frappe.new_doc("Production Order")
	po.production_item = cm_po.box
	box_details = frappe.get_doc("CM Box Description", cm_po.box_desc)
	po.bom_no = box_details.item_bom
	po.posting_date = cm_po.mfg_date
	po.sales_order = cm_po.sales_order
	po.skip_transfer = True
	po.qty = cm_po.mfg_qty
	po.wip_warehouse = po.source_warehouse = frappe.db.get_single_value("Manufacturing Settings", "default_wip_warehouse")
	po.fg_warehouse = frappe.db.get_single_value("Manufacturing Settings", "default_fg_warehouse")
	po.submit()
	print "Created production order {0} for {1} of quantity {2}".format(po.name, po.production_item, po.qty)
	return po.name

def submit_sales_order(sales_order):
	if (sales_order is None): return
	order_doc = frappe.get_doc("Sales Order", sales_order)
	if (order_doc.status == 'Draft'):
		order_doc.submit()
=======
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
			roll = get_suitable_roll(paper.rm, paper.rm_type, planned_qty, added_rolls, available_rolls)

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
		if (roll.status != "Ready" or roll.paper != paper): continue
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
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a

@frappe.whitelist()
def create_new_stock_entry(cm_po):
	orders = frappe.get_all("Production Order", fields={"production_item":cm_po.box, "sales_order":cm_po.sales_order})
<<<<<<< HEAD
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
	se.set_posting_time = True
	se.posting_date = cm_po.mfg_date
	#for item in se.items:
	#	print "Item:{0} Quantity:{1}".format(item.item_code, item.qty)
	se.submit()

	return se.name
=======
	if len(orders) > 0: po = orders[0]
	else: frappe.throw("Unable to find the production order for sales_order {0}".format(cm_po.sales_order))

	stock_entry = make_stock_entry(po.name, "Manufacture", po.qty)
	se = frappe.new_doc("Stock Entry")
	se.update(stock_entry)

	update_paper_quantity(cm_po, se)
	se.calculate_rate_and_amount()
	se.submit()

	update_production_roll_qty(cm_po)
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a

@frappe.whitelist()
def check_material_availability(cm_po):
	#try to use the stock_entry functionality
	pass

@frappe.whitelist()
<<<<<<< HEAD
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

@frappe.whitelist()
def filter_boards(doctype, txt, searchfield, start, page_len, filters):
	return get_filtered_boards(txt, filters)

def get_filtered_boards(txt, filters):
	box_desc = frappe.get_doc("CM Box Description", filters["box_desc"])
	layer_type = filters["layer_type"]
	ignore_bom = filters["ignore_bom"]

	deck_filter = ""
	if (not ignore_bom):
		deck_filter = "and item_code LIKE '{0}%%'".format(box_desc.get_board_prefix(layer_type))
	filter_query =	"""select name from `tabItem`
						where item_group='Board Layer'
						{0}
						and name LIKE %(txt)s
					""".format(deck_filter)
	#print "Searching boards matching {0} with query {1} and text {2}".format(box_desc.get_board_prefix(layer_type), filter_query, txt)
	boards = frappe.db.sql(filter_query, {"txt": "%%%s%%" % txt})
	filtered_boards = []
	for (board, ) in boards:
		qty = get_latest_stock_qty(board)
		if (qty > 0):
			filtered_boards.append((board, qty))
	return filtered_boards
=======
def make_new_stock_entry(source_name):
	cm_po = frappe.get_doc("CM Production Order", source_name)
	print("Creating PO for CM Order {0}".format(cm_po.name))

	se = create_stock_entry(cm_po)

	return se.as_dict()
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
