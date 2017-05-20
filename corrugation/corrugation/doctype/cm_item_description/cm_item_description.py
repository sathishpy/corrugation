# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class CMItemDescription(Document):
	def autoname(self):
		self.name = self.item + "-description"

	def on_submit(self):
		pass

@frappe.whitelist()
def make_new_bom(source_name):
	print "Creating new bom"
	item = frappe.get_doc("CM Item Description", source_name)

	sheet_length = float(item.sheet_length)
	sheet_width = float(item.sheet_width)

	paper_measurements = item.item_rm_bottom.split("-")
	size = len(paper_measurements)
	gsm = float(paper_measurements[size-3])
	bf = paper_measurements[size-2]
	deck = float(paper_measurements[size-1])

	weight_top  = float((sheet_length * sheet_width / 10000) * gsm/1000)
	flute = float(item.item_flute)
	weight_bottom = weight_top + weight_top * flute
	weight = weight_top + weight_bottom
	print "Paper measurement gsm={0} bf={1} deck={2} weight={3}kg".format(gsm, bf, deck, weight)

	l_wastage = (deck - sheet_length)
	w_wastage = (deck - sheet_width)
	wastage = (w_wastage * 100/deck)
	if (l_wastage > 0 and l_wastage < w_wastage):
		wastage = (l_wastage * 100/ deck)
	bom = frappe.new_doc("BOM")
	bom.item = item.item
	bom.item_name = item.item_name
	bom.quantity = 100

	bom_item = frappe.new_doc("BOM Item")
	bom_item.item_code = item.item_rm_bottom
	bom_item.qty = bom.quantity * weight_bottom
	paper_item = frappe.get_doc("Item", item.item_rm_bottom)
	print "retrieved ite {0}".format(paper_item.name)
	bom_item.rate = paper_item.valuation_rate
	if (bom_item.rate == 0):
		bom_item.rate = paper_item.standard_rate
	bom_item.scrap = wastage
	bom_item.stock_uom = paper_item.stock_uom
	bom.append("items", bom_item)

	bom_item = frappe.new_doc("BOM Item")
	bom_item.item_code = item.item_rm_top
	bom_item.qty = bom.quantity * weight_top
	paper_item = frappe.get_doc("Item", item.item_rm_top)
	bom_item.rate = paper_item.valuation_rate
	if (bom_item.rate == 0):
		bom_item.rate = paper_item.standard_rate
	bom_item.scrap = wastage
	bom_item.stock_uom = paper_item.stock_uom
	bom.append("items", bom_item)

	bom_item = frappe.new_doc("BOM Item")
	bom_item.item_code = item.item_rm_gum
	bom_item.qty = bom.quantity * weight_bottom * 0.20
	rm_item = frappe.get_doc("Item", item.item_rm_gum)
	bom_item.rate = rm_item.valuation_rate
	if (bom_item.rate == 0):
		bom_item.rate = rm_item.standard_rate
	bom_item.stock_uom = rm_item.stock_uom
	bom.append("items", bom_item)

	bom_item = frappe.new_doc("BOM Item")
	bom_item.item_code = item.item_rm_ink
	bom_item.qty = bom.quantity * weight_top * 0.10
	rm_item = frappe.get_doc("Item", item.item_rm_ink)
	bom_item.rate = rm_item.valuation_rate
	if (bom_item.rate == 0):
		bom_item.rate = rm_item.standard_rate
	bom_item.stock_uom = rm_item.stock_uom
	bom.append("items", bom_item)

	return bom
