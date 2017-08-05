	# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class CMBoxDescription(Document):
	def autoname(self):
		items = frappe.db.sql_list("""select name from `tabCM Box Description` where item=%s""", self.item)
		if items:
			idx = len(items) + 1
		else:
			idx = 1
		self.name = self.item + "-DESC" + ('-%.3i' % idx)

	def add_paper_item(self, layer):
		colour = "Brown"
		if "White" in self.item_top_type and layer == "Top":
			colour = 'White'

		rm_item = frappe.new_doc("CM Paper Item")
		rm_item.rm_type = layer
		papers = get_layer_papers(self.sheet_length, self.sheet_width, colour)
		if (len(papers) > 0):
			print "Assigning paper {0} for {1}".format(papers[0], layer)
			paper, deck = papers[0]
			rm_item.rm = paper
		self.append("item_papers", rm_item)

	def populate_paper_materials(self):
		self.sheet_length = 2 * (self.item_width + self.item_length + self.item_cutting_margin) + self.item_pin_lap
		self.sheet_width = self.item_per_sheet * (self.item_width + self.item_height) + 2 * self.item_cutting_margin

		count, self.item_papers = 1, []
		self.add_paper_item("Top")
		while count < int(self.item_ply_count):
			self.add_paper_item("Flute")
			self.add_paper_item("Liner")
			count += 2

	def populate_misc_materials(self, rm_type, rm, percent):
		rm_item = frappe.new_doc("CM Misc Item")
		rm_item.rm_type = rm_type
		rm_item.rm = rm
		rm_item.rm_percent = percent
		self.append("item_others", rm_item)

	def populate_raw_materials(self):
		if (self.box is None): return
		self.populate_paper_materials()

		self.item_others = []
		other_items = [("Corrugation Gum", "CRG-GUM", 2), ("Pasting Gum", "PST-GUM", 3)]
		if ("Print" in self.item_top_type):
			other_items.append(("Printing Ink", "INK-BLUE", 0.3))
		for (rm_type, rm, percent) in other_items:
			self.populate_misc_materials(rm_type, rm, percent)
		self.update_cost()

	def validate(self):
		if (int(self.item_ply_count) != len(self.item_papers)):
			frappe.trow("Not all box layers added as paper items")

		expected_type = "Top"
		for paper in self.item_papers:
			if (paper.rm_type != expected_type):
				frappe.throw("Paper Type in Item description should follow the order Top, Flute and Liner")
			if (paper.rm_type == "Top" or paper.rm_type == "Liner"):
				expected_type = "Flute"
			else:
				expected_type = "Liner"

	def get_paper_weight(self, paper):
		if paper is None: return 0
		(gsm, bf, deck) = get_paper_measurements(paper)
		weight = float((self.sheet_length * deck) * gsm/1000)/10000
		print ("Weight of length:{0} deck:{1} gsm:{2} is {3}".format(self.sheet_length, deck, gsm, weight))
		return weight

	def get_box_layer_weight(self, paper):
		if paper is None: return 0
		(gsm, bf, deck) = get_paper_measurements(paper)
		box_length = self.sheet_length - (2 * self.item_cutting_margin)
		box_width = self.sheet_width - (2 * self.item_cutting_margin)
		weight = float((box_length * box_width) * gsm/1000)/10000
		return weight

	def update_layers(self, rm_type, rm):
		if (self.same_layers):
			print("Updating all {0} layers to {1}".format(rm_type, rm))
			for item in self.item_papers:
				if item.rm_type == rm_type:
					item.rm = rm
		self.update_cost()

	def update_cost(self):
		box = frappe.get_doc("CM Box", self.box)
		self.item_rate = box.box_rate
		self.item_paper_cost, self.item_misc_cost = 0, 0
		paper_weight = 0
		for item in self.item_papers:
			if item.rm is None: continue
			if (item.rm_type == 'Top' or item.rm_type == 'Liner'):
				item.rm_rate = get_item_rate(item.rm, self.exclude_tax)
				item.rm_weight = float(self.get_paper_weight(item.rm)/self.item_per_sheet)
				item.rm_weight += (item.rm_weight * self.scrap_ratio)/100
				item.rm_cost = item.rm_rate * item.rm_weight
				self.item_paper_cost += item.rm_cost
				paper_weight += float(self.get_box_layer_weight(item.rm)/self.item_per_sheet)
			elif (item.rm_type == 'Flute'):
				item.rm_rate = get_item_rate(item.rm, self.exclude_tax)
				item.rm_weight = float((self.get_paper_weight(item.rm) * self.item_flute)/self.item_per_sheet)
				item.rm_weight += (item.rm_weight * self.scrap_ratio)/100
				item.rm_cost = item.rm_rate * item.rm_weight
				self.item_paper_cost += item.rm_cost
				paper_weight += float((self.get_box_layer_weight(item.rm) * self.item_flute)/self.item_per_sheet)
			print "Cost of rm {0} having weight {1} is {2}".format(item.rm, item.rm_weight, item.rm_cost)

		misc_weight = 0
		for item in self.item_others:
			if item.rm is None: continue
			item.rm_rate = get_item_rate(item.rm, self.exclude_tax)
			item.rm_weight = paper_weight * item.rm_percent / 100
			item.rm_weight += (item.rm_weight * self.scrap_ratio)/100
			item.rm_cost = item.rm_weight * item.rm_rate
			misc_weight += item.rm_weight
			self.item_misc_cost += item.rm_cost
			print "Cost of rm {0} having weight {1} is {2}".format(item.rm, item.rm_weight, item.rm_cost)

		#Assume about 70% of GUM/Ink will be dried/wasted
		self.item_weight = paper_weight + misc_weight * 0.3
		print("Paper cost={0} Misc cost={1} items={2}".format(self.item_paper_cost, self.item_misc_cost, self.item_per_sheet))
		if (self.item_paper_cost == 0): return

		total_expense = get_total_expenses(0)
		(boxes, production) = get_production_details(0)
		print("Boxes = {0} production={1} expense={2}".format(boxes, production, total_expense))
		if (boxes != 0 and self.item_prod_cost == 0): self.item_prod_cost = total_expense/boxes
		#self.item_rate = get_item_rate(self.item)
		self.item_total_cost = float(self.item_paper_cost + self.item_misc_cost + self.item_prod_cost + self.item_transport_cost)
		interest_loss = float(self.item_rate * self.credit_rate * self.credit_period)/1200
		self.item_profit_amount = self.item_rate - (self.item_total_cost + interest_loss)
		self.item_profit = float(self.item_profit_amount*100/self.item_total_cost)

	def get_board_name(self, layer_no):
		idx = layer_no - 1
		board_name = None
		if (idx == 0):
			board_name = "Layer-Top-{0:.1f}-{1:.1f}".format(self.sheet_length, self.sheet_width)
			paper_elements = self.item_papers[idx].rm.split("-")
			board_name += "-" + paper_elements[2] + "-" + paper_elements[3] + "-" + paper_elements[4]
		else:
			board_name = "Layer-Flute-{0:.1f}-{1:.1f}".format(self.sheet_length, self.sheet_width)
			paper_elements = self.item_papers[idx-1].rm.split("-")
			board_name += "-" + paper_elements[2] + "-" + paper_elements[3] + "-" + paper_elements[4]
			paper_elements = self.item_papers[idx].rm.split("-")
			board_name += "-" + paper_elements[2] + "-" + paper_elements[3] + "-" + paper_elements[4]
		return board_name

	def get_all_boards(self):
		layer, boards = 1, []
		while layer <= int(self.item_ply_count):
			boards += [self.get_board_name(layer)]
			layer += 2
		return boards

	def create_board_item(self, layer_no, rate):
		boardname = self.get_board_name(layer_no)
		board = frappe.db.get_value("Item", filters={"name": boardname})
		if board is not None: return board

		item = frappe.new_doc("Item")
		item.item_code = item.item_name = boardname
		item.item_group = "Board Layer"
		item.valuation_rate = rate
		item.weight_uom = "Kg"
		item.is_sales_item = False
		item.save()
		return item.name

	def make_board_items(self):
		layer, boards = 1, []
		while layer <= int(self.item_ply_count):
			item = self.item_papers[layer-1]
			valuation_rate = item.rm_cost
			if (item.rm_type == 'Flute'):
				layer += 1
				item = self.item_papers[layer-1]
				valuation_rate += item.rm_cost
			boards += [self.create_board_item(layer, valuation_rate)]
			layer += 1
		return boards

	def make_new_bom(self):
		bom = frappe.new_doc("BOM")
		bom.item = self.item
		bom.item_name = self.item_name
		bom.quantity, bom.items = 1, []

		for item in (self.item_papers + self.item_others):
			if item.rm is None: continue

			quantity = (bom.quantity * item.rm_weight)/int(self.item_per_sheet)
			print ("Updating Item {0} of quantity {1}".format(item.rm, quantity))

			if (len(bom.items) > 0):
				bom_item = next((bi for bi in bom.items if bi.item_code == item.rm), None)
				if bom_item is not None:
					bom_item.qty += quantity
					continue

			bom_item = frappe.new_doc("BOM Item")
			bom_item.item_code = item.rm
			bom_item.stock_qty = bom_item.qty = quantity
			bom_item.rate = get_item_rate(item.rm)
			rm_item = frappe.get_doc("Item", item.rm)
			bom_item.stock_uom = rm_item.stock_uom
			bom.append("items", bom_item)

		bom.base_operating_cost = bom.operating_cost = bom.quantity * self.item_prod_cost
		bom.save()
		print "Creating new bom {0} for {1} with operating cost {2}".format(bom.name, bom.item_name, bom.operating_cost)
		bom.submit()
		self.item_bom = bom.name

	def before_save(self):
		self.update_cost()

	def before_submit(self):
		self.make_new_bom()

	def on_submit(self):
		boards = self.make_board_items()
		print("Created item decsription {0} with bom {1}".format(self.name, self.item_bom))

	def update_cost_after_submit(self):
		self.update_cost();
		self.save(ignore_permissions=True)

def get_paper_measurements(paper):
	(gsm, bf, deck) = (0, 0, 0)
	item = frappe.get_doc("Item", paper)
	for attribute in item.attributes:
		if attribute.attribute == "GSM":
			gsm = int(attribute.attribute_value)
		elif attribute.attribute == "BF":
			bf = int(attribute.attribute_value)
		elif attribute.attribute == "Deck":
			deck = float(attribute.attribute_value)
	return (gsm, bf, deck)

@frappe.whitelist()
def get_item_rate(item_name, exclude_tax=True):
	std_rate = frappe.db.get_value("Item", item_name, "standard_rate")
	landing_rate = frappe.db.get_value("Item", item_name, "valuation_rate")
	if (std_rate is None and landing_rate is None): return 0
	if (not exclude_tax): return max(std_rate, landing_rate)
	if (std_rate == 0): std_rate = landing_rate * 0.88
	extra_charges = max(0, (landing_rate - (std_rate * 1.12)))
	print("Item {0} standard rate:{1} valuation rate:{2} charges:{3}".format(item_name, std_rate, landing_rate, extra_charges))
	return (std_rate + extra_charges)

def get_total_expenses(month):
	expenses = frappe.get_all("Journal Entry", fields={"voucher_type":"Journal Entry"})
	expense_total = 0

	for expense_entry in expenses:
		expense = frappe.get_doc("Journal Entry", expense_entry.name)
		#print("{0}    {1}".format(expense.title, expense.total_debit))
		expense_total += expense.total_debit

	return expense_total

def get_production_details(month):
	prod_orders = frappe.get_all("Production Order", fields={"status":"Completed"})
	total_boxes = total_production = 0

	for order_entry in prod_orders:
		order = frappe.get_doc("Production Order", order_entry.name)
		stock_entry = frappe.get_doc("Stock Entry", {"production_order":order.name})
		total_boxes += order.produced_qty
		total_production += stock_entry.total_outgoing_value

	return (total_boxes, total_production)

@frappe.whitelist()
def get_no_of_boards_for_box(box_desc_name, layer, box_count):
	box_desc = frappe.get_doc("CM Box Description", box_desc_name)
	boards = box_count/box_desc.item_per_sheet
	if (layer != "Top"):
		boards = boards * int(int(box_desc.item_ply_count)/2)
	return boards

@frappe.whitelist()
def get_no_of_boxes_from_board(box_desc_name, layer, boards):
	box_desc = frappe.get_doc("CM Box Description", box_desc_name)
	if (layer != "Top"):
		boards = boards/int(int(box_desc.item_ply_count)/2)
	box_count = boards * box_desc.item_per_sheet
	return box_count

@frappe.whitelist()
def get_planned_paper_quantity(box_desc, rmtype, paper, mfg_qty):
	box_details = frappe.get_doc("CM Box Description", box_desc)
	for paper_item in box_details.item_papers:
		if paper_item.rm_type == rmtype and (paper is None or paper_item.rm == paper):
			return paper_item.rm_weight * mfg_qty
	return 0

@frappe.whitelist()
def is_layer_compatible(box_desc1, box_desc2, layers):
	print ("Comparing desc {0} with {1} for layer {2}".format(box_desc1, box_desc2, layers))
	papers1 = frappe.get_doc("CM Box Description", box_desc1).item_papers
	papers2 = frappe.get_doc("CM Box Description", box_desc2).item_papers
	for idx in range(0, len(papers1)):
		if papers1[idx].rm_type in layers:
			if (papers1[idx].rm != papers2[idx].rm):
				print ("Paper {0} for {1} doesn't match {2}".format(papers1[idx].rm, papers1[idx].rm_type, papers2[idx].rm))
				return False
	return True

@frappe.whitelist()
def filter_papers(doctype, txt, searchfield, start, page_len, filters):
	sheet_length = filters["sheet_length"]
	sheet_width = filters["sheet_width"]
	layer_type = filters["layer_type"]
	colour = 'Brown'
	if layer_type == "Top" and "White" in filters["top_type"]:	colour = 'White'
	return get_layer_papers(sheet_length, sheet_width, colour, txt)

def get_layer_papers(sheet_length, sheet_width, colour, txt=""):
	filter_query =	"""select item.name, attr.attribute_value
						from tabItem item left join `tabItem Variant Attribute` attr
						on (item.name=attr.parent)
						where item.docstatus < 2
							and item.variant_of='PPR'
							and item.disabled=0
							and (attr.attribute='Deck' and
									((attr.attribute_value >= {0} and attr.attribute_value <= {1})
										or (attr.attribute_value >= {2} and attr.attribute_value <= {3})
									)
								)
							and exists (
									select name from `tabItem Variant Attribute` iv_attr
									where iv_attr.parent=item.name
										and (iv_attr.attribute='Colour' and iv_attr.attribute_value = '{4}')
									)
							and item.name LIKE %(txt)s
						order by attr.attribute_value * 1 asc
					""".format(sheet_length, sheet_length+10, sheet_width, sheet_width+10, colour)
	#print "Searching papers matching deck {0} with query {1}".format(sheet_length, filter_query)
	return frappe.db.sql(filter_query, {"txt": "%%%s%%" % txt})
