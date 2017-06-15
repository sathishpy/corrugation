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

		self.name = self.item + "-description" + ('-%.3i' % idx)

	def on_submit(self):
		pass

	def populate_paper_materials(self):
		self.item_papers = []
		rm_item = frappe.new_doc("CM Paper Item")
		rm_item.rm_type = 'Top Paper'
		self.append("item_papers", rm_item)
		print ("Ply count {0}".format(self.item_ply_count))
		if (int(self.item_ply_count) == 5):
			print ("Adding additional layers")
			rm_item = frappe.new_doc("CM Paper Item")
			rm_item.rm_type = 'Flute Liner Paper'
			self.append("item_papers", rm_item)

			rm_item = frappe.new_doc("CM Paper Item")
			rm_item.rm_type = "Liner Paper"
			self.append("item_papers", rm_item)

		rm_item = frappe.new_doc("CM Paper Item")
		rm_item.rm_type = 'Flute Paper'
		self.append("item_papers", rm_item)

		rm_item = frappe.new_doc("CM Paper Item")
		rm_item.rm_type = "Bottom Paper"
		self.append("item_papers", rm_item)

	def populate_raw_materials(self):
		self.populate_paper_materials()

		rm_item = frappe.new_doc("CM Misc Item")
		rm_item.rm_type = "Corrugation Gum"
		rm_item.rm_percent = 3
		self.append("item_others", rm_item)

		rm_item = frappe.new_doc("CM Misc Item")
		rm_item.rm_type = "Pasting Gum"
		rm_item.rm_percent = 2
		self.append("item_others", rm_item)

		rm_item = frappe.new_doc("CM Misc Item")
		rm_item.rm_type = "Printing Ink"
		rm_item.rm_percent = 0.3
		self.append("item_others", rm_item)

	def populate_raw_materals_check(self):
		if len(self.item_papers) != 0 or len(self.item_others) != 0: return
		self.populate_raw_materals()

	def get_overall_cost(self):
		(top_weight, top_cost) = get_paper_weight_cost(self.item_rm_top)
		(flute_weight, flute_cost) = get_paper_weight_cost(self.item_rm_flute)
		(bottom_weight, bottom_cost) = get_paper_weight_cost(self.item_rm_bottom)
		paper_cost = top_cost + flute_cost + bottom_cost
		operating_cost = paper_cost * 0.1
		return (paper_cost, operating_cost)

	def get_paper_weight_cost(self, paper):
		if paper is None: return (0, 0)
		(gsm, bf, deck) = get_paper_measurements(paper)
		print ("Sheet {0} sl={1} sw={2} deck={3}".format(gsm, self.sheet_length, self.sheet_width, deck))
		weight = float((self.sheet_length * self.sheet_width)/10000 * gsm)/1000
		cost = weight * get_item_rate(paper)
		print("Paper {0} weight={1} rate={2} cost={3}".format(paper, weight, get_item_rate(paper), cost))
		return (weight, cost)

	def validate(self):
		pass

	def on_update(self):
		self.update_cost()

	def before_submit(self):
		self.item_bom = make_new_bom(self.name)
		print("Created item decsription {0} with bom {1}".format(self.name, self.item_bom))

	def update_cost(self):
		rms_cost = 0
		paper_weight = 0
		for item in self.item_papers:
			if item.rm is None: return
			if (item.rm_type == 'Top Paper' or item.rm_type == 'Bottom Paper' or item.rm_type == 'Liner Paper'):
				(item.rm_weight, item.rm_cost) = self.get_paper_weight_cost(item.rm)
				rms_cost += item.rm_cost
				paper_weight += item.rm_weight
			elif (item.rm_type == 'Flute Paper' or item.rm_type == 'Flute Liner Paper'):
				(weight, cost) = self.get_paper_weight_cost(item.rm)
				item.rm_weight = weight * self.item_flute
				item.rm_cost = cost * self.item_flute
				rms_cost += item.rm_cost
				paper_weight += item.rm_weight
			print "Cost of rm {0} having weight {1} is {2}".format(item.rm, item.rm_weight, item.rm_cost)

		for item in self.item_others:
			if item.rm is None: return
			item.rm_weight = paper_weight * item.rm_percent / 100
			item.rm_cost = item.rm_weight * get_item_rate(item.rm)
			rms_cost += item.rm_cost
			print "Cost of rm {0} having weight {1} is {2}".format(item.rm, item.rm_weight, item.rm_cost)

		print("Raw Material cost={0} items={1}".format(rms_cost, self.item_per_sheet))
		self.item_rm_cost = rms_cost/int(self.item_per_sheet)
		total_expense = get_total_expenses(0)
		(boxes, production) = get_production_details(0)
		print("Boxes = {0} production={1}".format(boxes, production))
		if (boxes != 0): self.item_prod_cost = total_expense/boxes
		self.item_total_cost = float(self.item_rm_cost + self.item_prod_cost)
		self.item_profit = float((get_item_rate(self.item) - self.item_total_cost)*100/self.item_total_cost)
		print("RM cost={0} OP Cost={1} Rate={2}".format(self.item_rm_cost, self.item_prod_cost, get_item_rate(self.item) ))

def get_paper_measurements(paper):
	(gsm, bf, deck) = (0, 0, 0)
	item = frappe.get_doc("Item", paper)
	for attribute in item.attributes:
		if attribute.attribute == "GSM":
			gsm = int(attribute.attribute_value)
		elif attribute.attribute == "BF":
			bf = int(attribute.attribute_value)
		elif attribute.attribute == "Deck":
			deck = int(attribute.attribute_value)
	return (gsm, bf, deck)

def get_paper_measurements_old(paper):
	paper_measurements = paper.split("-")
	size = len(paper_measurements)
	gsm = float(paper_measurements[size-3])
	bf = paper_measurements[size-2]
	deck = float(paper_measurements[size-1])
	return (gsm, bf, deck)

def get_item_rate(item_name):
	item = frappe.get_doc("Item", item_name)
	rate = item.valuation_rate
	if (rate == 0):
		rate = item.standard_rate
	return rate

def get_total_expenses(month):
	expenses = frappe.get_all("Journal Entry", fields={"voucher_type":"Journal Entry"})
	expense_total = 0

	for expense_entry in expenses:
		expense = frappe.get_doc("Journal Entry", expense_entry.name)
		print("{0}    {1}".format(expense.title, expense.total_debit))
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
def make_new_bom(source_name):
	item_desc = frappe.get_doc("CM Box Description", source_name)

	bom = frappe.new_doc("BOM")
	bom.item = item_desc.item
	bom.item_name = item_desc.item_name
	bom.quantity = 1

	list_empty = True

	for item in (item_desc.item_papers + item_desc.item_others):
		if item.rm is None: continue

		quantity = (bom.quantity * item.rm_weight)/int(item_desc.item_per_sheet)
		print ("Updating Item {0} of quantity {1}".format(item.rm, quantity))

		if (list_empty is False):
			bom_item = next((bi for bi in bom.items if bi.item_code == item.rm), None)
			if bom_item is not None:
				bom_item.qty += quantity
				continue

		bom_item = frappe.new_doc("BOM Item")
		bom_item.item_code = item.rm
		bom_item.qty = quantity
		bom_item.rate = get_item_rate(item.rm)
		rm_item = frappe.get_doc("Item", item.rm)
		bom_item.stock_uom = rm_item.stock_uom
		bom.append("items", bom_item)
		list_empty = False

	bom.base_operating_cost = bom.operating_cost = bom.quantity * item_desc.item_prod_cost
	bom.save()
	print "Creating new bom {0} for {1} with operating cost {2}".format(bom.name, bom.item_name, bom.operating_cost)
	bom.submit()
	return bom.name
