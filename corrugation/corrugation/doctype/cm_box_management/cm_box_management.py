# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from operator import itemgetter

class CMBoxManagement(Document):
	def autoname(self):
		self.name = "Box Management"

	def populate_box_profit(self):
		boxes = frappe.db.sql("""select box.name, box.box_rate, bom.name
									from `tabCM Box` box left join `tabCM Box Description` bom
									on bom.box = box.name
									order by bom.item_profit_amount * 1 asc""")
		self.box_profit_items = []
		self.box_count = self.paper_count = 0
		unique_papers = []
		for (box_name, box_rate, box_desc) in boxes:
			if box_rate == 0 and not self.include_all: continue
			if (box_desc is None): continue

			box_item = frappe.new_doc("CM Box Profit Item")
			box_item.box = box_name
			box_item.box_rate = box_rate
			box_item.box_desc = box_desc
			box_desc = frappe.get_doc("CM Box Description", box_item.box_desc)
			box_item.board = "{0}-{1}".format(box_desc.sheet_length, box_desc.sheet_width)
			box_item.profit = box_desc.item_profit_amount
			box_item.top_paper = next((paper.rm for paper in box_desc.item_papers if paper.rm_type == "Top"), None)
			box_item.flute_paper = next((paper.rm for paper in box_desc.item_papers if paper.rm_type == "Flute"), None)
			box_item.liner_paper = next((paper.rm for paper in box_desc.item_papers if paper.rm_type == "Liner"), None)
			papers = set([box_item.top_paper, box_item.flute_paper, box_item.liner_paper])
			paper_list = [str(paper)[4:] for paper in papers]
			box_item.papers = ", ".join(paper_list)
			unique_papers += list(papers)
			#print("Processing box {0}".format(box_item.box))
			self.append("box_profit_items", box_item)
			self.box_count += 1

		self.paper_count += len(list(set(unique_papers)))

	def populate_box_capacity(self):
		boxes = frappe.db.sql("""select box.name, bom.name
									from `tabCM Box` box left join `tabCM Box Description` bom
									on bom.box = box.name""")
		self.box_capacity_items = []
		for (box_name, box_desc) in boxes:
			if (box_desc is None): continue

			box_item = frappe.new_doc("CM Box Capacity Item")
			box_item.box = box_name
			box_item.box_desc = box_desc
			box_desc = frappe.get_doc("CM Box Description", box_item.box_desc)
			top_paper = next((paper.rm for paper in box_desc.item_papers if paper.rm_type == "Top"), None)
			flute_paper = next((paper.rm for paper in box_desc.item_papers if paper.rm_type == "Flute"), None)
			liner_paper = next((paper.rm for paper in box_desc.item_papers if paper.rm_type == "Liner"), None)
			papers = set([top_paper, flute_paper, liner_paper])
			paper_list = [str(paper)[4:] for paper in papers]
			box_item.papers = ", ".join(paper_list)
			self.append("box_capacity_items", box_item)
