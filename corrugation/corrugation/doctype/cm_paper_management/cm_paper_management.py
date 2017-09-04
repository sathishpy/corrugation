# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from corrugation.corrugation.doctype.cm_box_description.cm_box_description import get_paper_attributes
from erpnext.controllers.item_variant import create_variant
from erpnext.controllers.item_variant import get_variant
from erpnext.stock.utils import get_latest_stock_qty
from operator import itemgetter

class CMPaperManagement(Document):
	def autoname(self):
		self.name = "Paper Management"

	def map_paper_to_boxes(self):
		self.paper_to_boxes = []
		boxes = frappe.db.sql("""select box.name, bom.name from `tabCM Box` box left join `tabCM Box Description` bom on bom.box = box.name""")
		paper_box_map = {}
		for (box, box_desc) in boxes:
			if (frappe.db.get_value("CM Box Description", box_desc) is None):
				frappe.throw("Failed to find the description {0} for box {1}".format(box_desc, box))
			box_desc = frappe.get_doc("CM Box Description", box_desc)
			for paper in box_desc.item_papers:
				if (paper_box_map.get(paper.rm) is None):
					paper_box_map[paper.rm] = set([box])
				else:
					paper_box_map[paper.rm].add(box)

		for (paper, boxes) in paper_box_map.items():
			paper_item = frappe.new_doc("CM PaperToBox Item")
			paper_item.paper = paper
			paper_item.box_count = len(boxes)
			paper_item.paper_qty = get_latest_stock_qty(paper)
			paper_item.boxes = ", ".join(boxes)
			paper_item.box_desc = frappe.db.get_value("CM Box Description", filters={"box": next(iter(boxes))})
			self.append("paper_to_boxes", paper_item)
		self.sort_on_box_count()

	def sort_paper_items(self, sort_type):
		paper_box_map = {}
		for paper_item in self.paper_to_boxes:
			paper_box_map[paper_item.paper] = paper_item

		sorted_items = []
		if (sort_type == "weight"):
			sorted_items = sorted(paper_box_map.keys(), key=lambda item: paper_box_map[item].paper_qty)
		elif (sort_type == "box-count"):
			sorted_items = sorted(paper_box_map.keys(), key=lambda item: paper_box_map[item].box_count)
		else:
			sorted_items = sorted(paper_box_map.keys(), key=lambda item: get_paper_deck(item))

		for counter in range(0, len(sorted_items)):
			paper_item = paper_box_map[sorted_items[counter]]
			paper_item.idx = counter+1

	def sort_on_weight(self):
		self.sort_paper_items("weight")

	def sort_on_box_count(self):
		self.sort_paper_items("box-count")

	def sort_on_deck(self):
		self.sort_paper_items("deck")

	def filter_boxes(self):
		self.map_paper_to_boxes()
		if (self.box_filter is None): return
		filtered_items = [item for item in self.paper_to_boxes if self.box_filter.lower() in item.boxes.lower()]
		self.paper_to_boxes = []
		print("Found {0} items matching {1}".format(len(filtered_items), self.box_filter))
		for counter in range(0, len(filtered_items)):
			paper_item = filtered_items[counter]
			paper_item.idx = counter + 1
			self.append("paper_to_boxes", paper_item)

	def update_paper_rate(self):
		for rate_item in self.paper_rates:
			from_gsm = int(rate_item.gsm.strip().split("-")[0])
			to_gsm = int(rate_item.gsm.strip().split("-")[1])
			if (from_gsm == 0):
				frappe.throw("GSM value is not in the right format")
			if (to_gsm == 0): to_gsm = from_gsm

			print("Getting all the papers matching color:{0} BF:{1} GSM:{2}-{3}".format(rate_item.colour, rate_item.bf, from_gsm, to_gsm))
			papers = get_papers(rate_item.colour, rate_item.bf, from_gsm, to_gsm)
			for paper in papers:
				std_rate = frappe.db.get_value("Item", paper, "standard_rate")
				landing_rate = std_rate = frappe.db.get_value("Item", paper, "valuation_rate")
				#print("Updating paper {0} rate from {1} to {2}".format(paper, std_rate, rate_item.std_rate))
				frappe.db.set_value("Item", paper, "standard_rate", rate_item.std_rate)
				frappe.db.set_value("Item", paper, "valuation_rate", rate_item.landing_rate)

				item_price = frappe.db.get_value("Item Price", filters={"item_code": paper, "price_list": "Standard Buying"})
				if (not item_price):
					price_doc = frappe.new_doc("Item Price")
					price_doc.update({"price_list": "Standard Buying", "item_code": paper, "price_list_rate": std_rate})
					price_doc.save()
				else:
					frappe.db.set_value("Item Price", item_price, "price_list_rate", std_rate)

		self.save()

	def check_paper(self):
		for new_paper in self.new_papers:
			attributes = new_paper.bf_gsm_deck.strip().split("-")
			if (len(attributes) != 3): continue
			args = {"Colour": new_paper.colour, "BF": attributes[0], "GSM": attributes[1], "Deck": attributes[2]}
			new_paper.paper = get_variant("PPR", args)

	def add_new_paper(self):
		for new_paper in self.new_papers:
			attributes = new_paper.bf_gsm_deck.strip().split("-")
			if (len(attributes) != 3):
				frappe.throw("Argume BF-GSM-Deck isn't in right format")
			args = {"Colour": new_paper.colour, "BF": attributes[0], "GSM": attributes[1], "Deck": attributes[2]}
			if (get_variant("PPR", args) != None):
				frappe.throw("Paper {0} is already present".format(new_paper.bf_gsm_deck))
			print("Creating the new paper {0}".format(args))
			paper = create_variant("PPR", args)
			paper.save()
			new_paper.paper = paper.name


@frappe.whitelist()
def get_papers(colour, bf, from_gsm, to_gsm):
	papers = frappe.db.get_all("Item", filters={"item_group": "Paper", "variant_of": "PPR"})
	filtered_papers = []
	for paper in papers:
		(p_colour, p_bf, p_gsm, p_deck) = get_paper_attributes(paper.name)
		#print("Paper {0} attributes color={0} bf={1} gsm={2}".format(p_colour, p_bf, p_gsm))
		if (colour == p_colour and bf == p_bf and p_gsm >= from_gsm and p_gsm <= to_gsm):
			filtered_papers.append(paper.name)
	return filtered_papers

def get_paper_deck(paper):
	if (paper is None): return 0
	(colour, bf, gsm, deck) = get_paper_attributes(paper)
	return deck
