# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import datetime
import calendar

class CMProductCosts(Document):
	def autoname(self):
		self.name = "Production Report {0}-{1}".format(self.cm_month, self.cm_year)

	def printUpdateCosts(self):
		print "Getting costs for {0}-{1}".format(self.cm_month, self.cm_year);
		prod_orders = frappe.get_all("Production Order", fields={"status":"Completed"})
		print("Prod Order Name    Production Item     Qunatity     BOM-Cost    Actual-Cost")
		for porder in prod_orders:
			order = frappe.get_doc("Production Order", porder.name)
			stock_entry = frappe.get_doc("Stock Entry", {"production_order":porder.name})
			bom = frappe.get_doc("BOM", order.bom_no)
			print ("{0}     {1}       {2}    {3}    {4}".format(order.name, order.production_item, order.produced_qty, (bom.base_total_cost/bom.quantity)*order.produced_qty, stock_entry.total_incoming_value))
			#print ("{0}     {1}       {2}    {3}    {4}".format(order.name, order.production_item, order.produced_qty, order.bom_no, stock_entry.total_incoming_value))
			print("SourceItem    DestItem    Quantity    Cost")
			for sitem in stock_entry.items:
				item = frappe.get_doc("Stock Entry Detail", sitem.name)
				if (item.s_warehouse is not None):
					print("{0}                {1}    {2}".format(item.item_name, item.qty, item.amount))
				else:
					print("            {0}    {1}    {2}".format(item.item_name, item.qty, item.amount))

	def updateCosts(self):
		#self.printUpdateCosts()
		month = list(calendar.month_abbr).index(self.cm_month)
		start_date = datetime.date(year=int(self.cm_year), month=month, day=1)
		end_date = datetime.date(year=int(self.cm_year), month=month, day=15)

		stock_entries = frappe.db.sql("""select name, posting_date, production_order
										from `tabStock Entry`
										where production_order is not NULL and posting_date between '{0}' and '{1}'"""\
										.format(start_date, end_date),as_dict=1)

		self.cm_act_indirect_cost = get_total_expenses(0)
		per_box_op_cost = get_op_cost_per_box(0)

		self.cm_est_direct_cost = self.cm_act_direct_cost = self.cm_total_production = 0
		self.product_cost = []

		for se in stock_entries:
			print ("--------------------------------------------------------------")
			print "Processing stock entry {0} on {1} for {2}".format(se.name, se.posting_date, se.production_order)

			order = frappe.get_doc("Production Order", se.production_order)
			stock_entry = frappe.get_doc("Stock Entry", se.name)
			bom = frappe.get_doc("BOM", order.bom_no)

			per_item_cost = bom.base_total_cost/bom.quantity
			print ("Item BOM Cost {0} Item Op Cost {1}".format(per_item_cost, per_box_op_cost))

			rm_cost = 0
			item_qty = 0
			for sitem in stock_entry.items:
				item = frappe.get_doc("Stock Entry Detail", sitem.name)
				if (item.s_warehouse is not None):
					rm_cost += item.amount
					print("RM:{0}    Price:{1}".format(item.item_name, item.amount))
				else:
					print("Item:{0}  Qty:{1}".format(item.item_name, item.qty))
					item_qty += item.qty

			if (item_qty == 0): continue

			product = frappe.new_doc("CM Product Cost")
			product.cm_product = order.production_item
			product.cm_date = se.posting_date
			product.cm_stock_info = se.name
			product.cm_bom_cost = per_item_cost * item_qty
			product.cm_act_cost = rm_cost + (per_box_op_cost * item_qty)
			product.cm_sales_price = stock_entry.total_incoming_value
			product.cm_int_loss = 0
			product.cm_profit = (product.cm_sales_price - product.cm_act_cost - product.cm_int_loss) * 100 / product.cm_act_cost
			self.append("product_cost", product)

			self.cm_est_direct_cost += product.cm_bom_cost
			self.cm_act_direct_cost += product.cm_act_cost
			self.cm_total_production += product.cm_sales_price

		self.save()

def get_op_cost_per_box(month):
	op_cost = get_total_expenses(month)
	(boxes, production) = get_production_details(month)
	return op_cost/boxes

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
