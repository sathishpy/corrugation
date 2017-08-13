# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from corrugation.corrugation.doctype.cm_box_description.cm_box_description import get_paper_attributes
from erpnext.controllers.item_variant import create_variant
from erpnext.controllers.item_variant import get_variant

class CMPaperManagementTool(Document):
	def autoname(self):
		self.name = "Paper Management"
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
				if (std_rate == rate_item.std_rate and landing_rate == rate_item.landing_rate): continue
				print("Updating paper {0} rate from {1} to {2}".format(paper, std_rate, rate_item.std_rate))
				frappe.db.set_value("Item", paper, "standard_rate", rate_item.std_rate)
				frappe.db.set_value("Item", paper, "valuation_rate", rate_item.landing_rate)
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
