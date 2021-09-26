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

	def add_paper_item(self, layer, quality = 0):
		colour = "Brown"
		if "White" in self.item_top_type and layer == "Top":
			colour = 'White'

		rm_item = frappe.new_doc("CM Paper Item")
		rm_item.rm_type = layer
		papers = get_layer_papers(layer, self.sheet_length, self.sheet_width, colour, "")
		paper = get_suitable_paper(papers, quality)
		#print ("Selected paper {0} for {1}".format(paper, layer))
		rm_item.rm = paper
		self.append("item_papers", rm_item)

	def update_sheet_values(self):
		box_type = frappe.db.get_value("CM Box", self.box, "box_type")
		if (box_type == "Universal"):
			self.sheet_length = 2 * (self.item_width + self.item_length + self.item_cutting_margin) + self.item_pin_lap
			self.sheet_width = self.item_per_sheet * (self.item_width + self.item_height) + 2 * self.item_cutting_margin
		elif (box_type == "MatchBox"):
			self.sheet_length = 2 * (self.item_width + self.item_height + self.item_cutting_margin) + self.item_pin_lap
			self.sheet_width = self.item_per_sheet * (self.item_length + 2 * self.item_height) + 2 * self.item_cutting_margin
		elif (box_type == "UniversalOpen"):
			self.sheet_length = 2 * (self.item_width + self.item_length + self.item_cutting_margin) + self.item_pin_lap
			self.sheet_width = self.item_per_sheet * (2 * self.item_pin_lap + self.item_height) + 2 * self.item_cutting_margin
		elif (box_type == "TopBottom"):
			self.sheet_length = (self.item_length + 2 * (self.item_height + self.item_cutting_margin))
			self.sheet_width = self.item_per_sheet *  (self.item_width + 2 * (self.item_height + self.item_cutting_margin))
		elif (box_type == "Top Plate" or box_type == "Flute Plate"):
			self.sheet_length = self.item_per_length * self.item_length + 2 * self.item_cutting_margin
			self.sheet_width = self.item_per_sheet * self.item_width + 2 * self.item_cutting_margin
		else:
			frappe.throw("Box Type {0} isn't supported yet".format(box_type))
		if (box_type != "Top Plate" and box_type != "Flute Plate"):
			self.sheet_length = self.item_per_length * self.sheet_length
		print("Sheet length and width for {0} boxes is {1}-{2}".format(self.item_per_sheet, self.sheet_length, self.sheet_width))
		#not really sheet related
		if (self.item_ply_count > 3):
			self.item_flute = 1.3
			self.scrap_ratio = 0.5
		if(self.swap_deck):
			self.sheet_width, self.sheet_length = self.sheet_length, self.sheet_width

	def populate_paper_materials(self, quality = 0):
		self.item_papers = []
		count = 1
		self.add_paper_item("Top", quality)
		while count < int(self.item_ply_count):
			self.add_paper_item("Flute", quality)
			self.add_paper_item("Liner", quality)
			count += 2
		self.update_rate_and_cost()

	def update_misc_items(self):
		misc_items = {"Corrugation Gum": ("CRG-GUM", 0.5), "Pasting Gum": ("PST-GUM", 3), "Glue": ("GLU-GUM", 0.13), "Printing Ink": ("INK-BLUE", 0.2), "Stitching Coil": ("STCH-COIL", 0.2)}
		for rm_item in self.item_others:
			if rm_item.rm: continue
			(rm, percent) = misc_items[rm_item.rm_type]
			rm_item.rm = rm
			rm_item.rm_percent = percent
		self.update_rate_and_cost()

	def populate_misc_materials(self):
		self.item_others = []
		items = ["Corrugation Gum", "Pasting Gum"]
		if ("Print" in self.item_top_type):
			items.append("Printing Ink")
		box_type = frappe.db.get_value("CM Box", self.box, "box_type")
		if ("Plate" not in box_type):
			if (not self.item_stitched): items.append("Glue")
			else: items.append("Stitching Coil")

		for rm_type in items:
			rm_item = frappe.new_doc("CM Misc Item")
			rm_item.rm_type = rm_type
			self.append("item_others", rm_item)
		self.update_misc_items()

	def populate_raw_materials(self):
		if (self.box is None): return
		self.item_others, self.item_papers = [], []
		self.update_sheet_values()

		box_type = frappe.db.get_value("CM Box", self.box, "box_type")
		if (box_type == "Top Plate"):
			self.add_paper_item("Top")
		else:
			self.populate_paper_materials()
			self.populate_misc_materials()

		self.update_rate_and_cost()
		self.adjust_paper_to_maintain_profit()

	def adjust_paper_to_maintain_profit(self):
		for counter in range(1, 3):
			saved_papers = self.item_papers
			profit = self.item_profit
			profit_aligned = True
			if (profit < 10):
				self.populate_paper_materials(-counter)
				if (self.item_profit < profit or self.item_profit > 10): profit_aligned = False
			elif (profit > 20):
				self.populate_paper_materials(counter)
				if (self.item_profit > profit or self.item_profit < 15): profit_aligned = False
			if (not profit_aligned):
				self.item_papers = saved_papers
				break

	def check_papers(self):
		if (int(self.item_ply_count) != len(self.item_papers)):
			frappe.throw("Not all box layers added as paper items")

		expected_type = "Top"
		for paper in self.item_papers:
			if (paper.rm_type != expected_type):
				frappe.throw("Paper Type in Item description should follow the order Top, Flute and Liner")
			if (paper.rm_type == "Top" or paper.rm_type == "Liner"):
				expected_type = "Flute"
			else:
				expected_type = "Liner"

	def get_paper_weight(self, paper, rm_type):
		if paper is None: return 0
		(color, bf, gsm, deck) = get_paper_attributes(paper)
		weight = float((self.sheet_length * deck) * gsm/1000)/10000
		if ("Top" in rm_type and deck >= self.sheet_length and self.sheet_length > self.sheet_width):
			weight = float((self.sheet_width * deck) * gsm/1000)/10000
		if ("Flute" in rm_type):
			weight = float(weight * self.item_flute)
		#print ("Weight of length:{0} deck:{1} gsm:{2} is {3}".format(self.sheet_length, deck, gsm, weight))
		return weight

	def get_box_layer_weight(self, paper, rm_type):
		if paper is None: return 0
		(color, bf, gsm, deck) = get_paper_attributes(paper)
		box_length = self.sheet_length - (2 * self.item_cutting_margin)
		box_width = self.sheet_width - (2 * self.item_cutting_margin)
		weight = float((box_length * box_width) * gsm/1000)/10000
		if ("Flute" in rm_type):
			weight = float(weight * self.item_flute)
		return weight

	def update_layers(self, rm_type, rm):
		if (self.same_layers):
			print("Updating all {0} layers to {1}".format(rm_type, rm))
			for item in self.item_papers:
				if item.rm_type == rm_type:
					item.rm = rm
		self.update_cost()

	def update_rate_and_cost(self):
		box = frappe.get_doc("CM Box", self.box)
		self.item_rate = box.box_rate
		for item in (self.item_papers + self.item_others):
			if item.rm is None: continue
			item.rm_rate = get_item_rate(item.rm, self.exclude_tax)
		self.update_cost()

	def update_box_rate(self):
		box = frappe.get_doc("CM Box", self.box)
		if (box.box_rate != self.item_rate):
			print("Changing box rate to {0}".format(self.item_rate))
			frappe.db.set_value("CM Box", self.box, "box_rate", self.item_rate)

	def update_cost(self):
		if (self.box is None): return
		self.item_paper_cost, self.item_misc_cost = 0, 0
		paper_weight = 0
		for item in self.item_papers:
			if item.rm is None: continue
			item.rm_weight = float(self.get_paper_weight(item.rm, item.rm_type)/self.get_items_per_board())
			item.rm_weight += (item.rm_weight * self.scrap_ratio)/100
			item.rm_cost = item.rm_rate * item.rm_weight
			self.item_paper_cost += item.rm_cost
			paper_weight += float(self.get_box_layer_weight(item.rm, item.rm_type)/self.get_items_per_board())
			#print "Cost of rm {0} having weight {1} is {2}".format(item.rm, item.rm_weight, item.rm_cost)

		misc_weight = 0
		for item in self.item_others:
			if item.rm is None: continue
			item.rm_weight = paper_weight * item.rm_percent / 100
			item.rm_weight += (item.rm_weight * self.scrap_ratio)/100
			item.rm_cost = item.rm_weight * item.rm_rate
			misc_weight += item.rm_weight
			self.item_misc_cost += item.rm_cost
			#print "Cost of rm {0} having weight {1} is {2}".format(item.rm, item.rm_weight, item.rm_cost)

		#Assume about 70% of GUM/Ink will be dried/wasted
		self.item_weight = paper_weight + misc_weight * 0.3
		if (frappe.db.get_value("CM Box", self.box, "box_type") == "Top Plate"):
			self.item_paper_cost = self.item_paper_cost/self.item_weight
		#print("Paper cost={0} Misc cost={1} items={2}".format(self.item_paper_cost, self.item_misc_cost, self.get_items_per_board()))
		if (self.item_paper_cost == 0): return

		self.item_prod_cost = self.get_production_cost()
		box_unit = float(self.item_length * self.item_width * self.item_height)/7000
		self.item_transport_cost = box_unit * 0.1
		#self.item_rate = get_item_rate(self.item)
		self.item_total_cost = float(self.item_paper_cost + self.item_misc_cost + self.item_prod_cost + self.item_transport_cost + self.item_other_cost)
		interest_loss = float(self.item_rate * self.credit_rate * self.credit_period)/1200
		self.item_profit_amount = self.item_rate - (self.item_total_cost + interest_loss)
		self.item_profit = float(self.item_profit_amount*100/self.item_total_cost)

	def get_items_per_board(self):
		return (self.item_per_sheet * self.item_per_length)

	def get_production_cost(self):
		if (frappe.db.get_value("CM Box", self.box, "box_type") == "Top Plate"): return 1

		layer_factor = (int(self.item_ply_count) - 1)/2
		item_per_sheet = float(self.get_items_per_board()) / layer_factor
		board_unit = float(self.sheet_width * self.sheet_length)/10000
		box_unit = float(self.item_length * self.item_width * self.item_height)/7000
		if (self.sheet_length > 175):
			board_unit = float(board_unit/2)
			item_per_sheet = float(item_per_sheet)/2
		corrugation_cost = (0.30 + board_unit * 0.10)/item_per_sheet
		pasting_cost = (0.20 + board_unit * 0.10)/item_per_sheet
		printing_cost = 0
		box_top_type = frappe.db.get_value("CM Box", self.box, "box_top_type")
		if ("Print" in box_top_type):
			printing_cost = (0.15 + board_unit * 0.10)/(item_per_sheet * layer_factor)
		punching_cost = (0.15 + board_unit * 0.10)/(item_per_sheet * layer_factor)
		if (self.item_is_slotted):
			punching_cost = (0.20 + board_unit * 0.15)/(item_per_sheet * layer_factor)
		glue_cost = 0.10 + box_unit * 0.05
		other_cost = 0.25 + box_unit * 0.10
		total_cost = corrugation_cost + pasting_cost + printing_cost + punching_cost + glue_cost + other_cost
		print("Prod Cost: crg={0} pst={1} prt={2} punch={3} glue={4} misc={5} unit={6}/{7}/{8}"
				.format(corrugation_cost, pasting_cost, printing_cost, punching_cost, glue_cost, other_cost, item_per_sheet, board_unit, box_unit))
		return (total_cost)

	def get_board_prefix(self, rmtype):
		return "Layer-{0}-{1:.1f}-{2:.1f}".format(rmtype, self.sheet_length, self.sheet_width)

	def get_board_name_from_papers(self, layer, papers):
		layers = ["Top"]
		if (layer != "Top"):
			layers = ["Flute", "Liner"]

		board_name = self.get_board_prefix(layer)
		for layer_type in layers:
			paper = next((paper for (rmtype, paper) in papers if layer_type == rmtype), None)
			if (paper == None):
				frappe.throw("Cannot find layer type {0} in rolls".format(layer_type))
			paper_elements = paper.split("-")
			board_name += "-" + paper_elements[2] + "-" + paper_elements[3]
		return board_name

	def get_all_boards(self):
		papers = [(paper.rm_type, paper.rm) for paper in self.item_papers]
		boards = [self.get_board_name_from_papers("Top", papers)]
		layer = 3
		while layer <= int(self.item_ply_count):
			boards += [self.get_board_name_from_papers("Flute", papers)]
			layer += 2
		return boards

	def create_board_item(self, boardname):
		board = frappe.db.get_value("Item", filters={"name": boardname})
		if board is not None: return board

		item = frappe.new_doc("Item")
		item.item_code = item.item_name = boardname
		item.item_group = "Board Layer"
		item.weight_uom = "Kg"
		item.is_sales_item = False
		print("Creating new board {0}".format(boardname))
		item.save()
		return item.name

	def make_board_items(self):
		papers = [(paper.rm_type, paper.rm) for paper in self.item_papers]
		layers = [paper.rm_type for paper in self.item_papers]
		if ("Top" in layers):
			boardname = self.get_board_name_from_papers("Top", papers)
			self.create_board_item(boardname)
		if ("Flute" in layers):
			boardname = self.get_board_name_from_papers("Flute", papers)
			self.create_board_item(boardname)

	def make_new_bom(self):
		bom = frappe.new_doc("BOM")
		bom.item = self.item
		bom.item_name = self.item_name
		bom.quantity, bom.items = 1, []

		for item in (self.item_papers + self.item_others):
			if item.rm is None: continue

			quantity = (bom.quantity * item.rm_weight)/int(self.get_items_per_board())
			#print ("Updating Item {0} of quantity {1}".format(item.rm, quantity))

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
		print ("Creating new bom {0} for {1} with operating cost {2}".format(bom.name, bom.item_name, bom.operating_cost))
		bom.submit()
		self.item_bom = bom.name

	def before_save(self):
		self.update_box_rate()
		self.update_cost()

	def before_submit(self):
		self.check_papers()
		self.make_new_bom()

	def on_submit(self):
		self.make_board_items()
		print("Created item decsription {0} with bom {1}".format(self.name, self.item_bom))

	def update_cost_after_submit(self):
		self.update_rate_and_cost();
		self.save(ignore_permissions=True)

	def add_new_paper(self, paper, color):
		from corrugation.corrugation.utils import create_new_paper
		new_paper = create_new_paper(paper, color)
		frappe.msgprint("Created papper {0}".format(new_paper))

@frappe.whitelist()
def get_paper_attributes(paper):
	(color, bf, gsm, deck) = (None, 0, 0, 0)
	item = frappe.get_doc("Item", paper)
	for attribute in item.attributes:
		if attribute.attribute == "GSM":
			gsm = int(attribute.attribute_value)
		elif attribute.attribute == "BF":
			bf = int(attribute.attribute_value)
		elif attribute.attribute == "Deck":
			deck = float(attribute.attribute_value)
		elif attribute.attribute == "Colour":
			color = attribute.attribute_value
	return (color, bf, gsm, deck)

@frappe.whitelist()
def get_item_rate(item_name, exclude_tax=True):
	std_rate = frappe.db.get_value("Item", item_name, "standard_rate")
	landing_rate = frappe.db.get_value("Item", item_name, "valuation_rate")
	if (std_rate is None and landing_rate is None): return 0
	if (not exclude_tax): return max(std_rate, landing_rate)
	if (std_rate == 0): std_rate = landing_rate * 0.88
	extra_charges = max(0, (landing_rate - (std_rate * 1.12)))
	#print("Item {0} standard rate:{1} valuation rate:{2} charges:{3}".format(item_name, std_rate, landing_rate, extra_charges))
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
	prod_orders = frappe.get_all("Work Order", fields={"status":"Completed"})
	total_boxes = total_production = 0

	for order_entry in prod_orders:
		order = frappe.get_doc("Work Order", order_entry.name)
		stock_entry = frappe.get_doc("Stock Entry", {"work_order":order.name})
		total_boxes += order.produced_qty
		total_production += stock_entry.total_outgoing_value

	return (total_boxes, total_production)

@frappe.whitelist()
def get_no_of_boards_for_box(box_desc_name, layer, box_count):
	box_desc = frappe.get_doc("CM Box Description", box_desc_name)
	boards = box_count/box_desc.get_items_per_board()
	if (layer != "Top"):
		boards = boards * int(int(box_desc.item_ply_count)/2)
	return boards

@frappe.whitelist()
def get_no_of_boxes_from_board(box_desc_name, layer, boards):
	box_desc = frappe.get_doc("CM Box Description", box_desc_name)
	if (layer != "Top"):
		boards = boards/int(int(box_desc.item_ply_count)/2)
	box_count = boards * box_desc.get_items_per_board()
	return box_count

@frappe.whitelist()
def get_planned_paper_quantity(box_desc, rmtype, paper, mfg_qty):
	box_details = frappe.get_doc("CM Box Description", box_desc)
	paper_qty = 0
	for paper_item in box_details.item_papers:
		if paper_item.rm_type == rmtype:
			if (paper is None or paper_item.rm == paper):
				paper_qty += paper_item.rm_weight * mfg_qty
			else:
				paper_qty += box_details.get_paper_weight(paper, rmtype)/box_details.get_items_per_board() * mfg_qty
	return paper_qty

@frappe.whitelist()
def is_layer_compatible(box_desc1, box_desc2, layers):
	#print ("Comparing desc {0} with {1} for layer {2}".format(box_desc1, box_desc2, layers))
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
	return get_layer_papers(layer_type, sheet_length, sheet_width, colour, txt)

def get_layer_papers(layer_type, sheet_length, sheet_width, colour, txt):
	deck_query = "(attr.attribute_value >= {0} and attr.attribute_value <= {1})".format(sheet_width, sheet_width+10)
	if (layer_type == "Top"):
		#Top direction doesn't matter
		deck_query += " or (attr.attribute_value >= {0} and attr.attribute_value <= {1})".format(sheet_length, sheet_length+10)

	filter_query =	"""select item.name, attr.attribute_value
						from tabItem item left join `tabItem Variant Attribute` attr
						on (item.name=attr.parent)
						where item.docstatus < 2
							and item.variant_of='PPR'
							and item.disabled=0
							and (attr.attribute='Deck' and ({0}))
							and exists (
									select name from `tabItem Variant Attribute` iv_attr
									where iv_attr.parent=item.name
										and (iv_attr.attribute='Colour' and iv_attr.attribute_value = '{1}')
									)
							and item.name LIKE %(txt)s
						order by attr.attribute_value * 1 asc
					""".format(deck_query, colour)
	#print "Searching papers matching deck {0} with query {1}".format(sheet_length, filter_query)
	papers = frappe.db.sql(filter_query, {"txt": "%%%s%%" % txt})
	return papers

def filter_papers_based_on_stock(papers):
	stock_based_papers = []
	for (paper, deck) in papers:
		rolls = frappe.db.sql("""select name from `tabCM Paper Roll` where paper='{0}' and weight > 50""".format(paper))
		if (len(rolls) > 0):
			stock_based_papers.append((paper, deck))
	return stock_based_papers

def get_suitable_paper(papers, quality):
	if (len(papers) == 0): return
	(suitable_paper, deck) = papers[0]
	(clr, last_bf, last_gsm, deck) = get_paper_attributes(suitable_paper)
	for (paper, deck) in papers[1:]:
		(clr, bf, gsm, deck) = get_paper_attributes(paper)
		#print ("Checking paper {0} at quality {1}".format(paper, quality))
		if (quality < 0 and (bf < last_bf or gsm < last_gsm)):
			quality += 1
			suitable_paper = paper
		if (quality > 0 and (bf > last_bf or gsm > last_gsm)):
			quality -= 1
			suitable_paper = paper
		if (quality == 0):
			break
		last_bf, last_gsm = bf, gsm
	return suitable_paper
