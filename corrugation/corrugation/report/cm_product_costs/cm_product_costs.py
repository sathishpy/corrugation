# Copyright (c) 2013, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import datetime
import calendar
from frappe import _


def execute(filters=None):
	columns = get_columns()
	entries = get_result(filters)
	for entry in entries:
		print entry

	return columns, entries

def get_result(filters=None):
	print filters

	start_date = filters.get("from_date")
	end_date = filters.get("to_date")

	act_indirect_cost = get_total_expenses(start_date, end_date)
	per_box_op_cost = get_op_cost_per_box(start_date, end_date)

	total_bom_rm_cost = total_bom_op_cost = total_act_rm_cost = total_act_op_cost = total_bom_cost = total_act_cost = total_production = 0
	result = []
	stock_entries = frappe.db.sql("""select name, posting_date, production_order
									from `tabStock Entry`
									where production_order is not NULL and posting_date between '{0}' and '{1}'"""\
									.format(start_date, end_date),as_dict=1)
	for se in stock_entries:
		order = frappe.get_doc("Production Order", se.production_order)
		stock_entry = frappe.get_doc("Stock Entry", se.name)
		bom_entries = frappe.db.sql("""select item_rm_cost, item_prod_cost
										from `tabCM Box Description`
										where item_bom='{0}'""".format(order.bom_no), as_dict=1)
		print bom_entries[0]

		act_rm_cost = 0
		item_qty = 0
		for sitem in stock_entry.items:
			item = frappe.get_doc("Stock Entry Detail", sitem.name)
			if (item.s_warehouse is not None):
				act_rm_cost += item.amount
			else:
				item_qty += item.qty

		if (item_qty == 0): continue

		bom_rm_cost = bom_entries[0].item_rm_cost * item_qty
		bom_op_cost = bom_entries[0].item_prod_cost * item_qty
		act_op_cost = per_box_op_cost * item_qty

		bom_cost = bom_rm_cost + bom_op_cost
		act_cost = act_rm_cost + act_op_cost

		sales_price = stock_entry.total_incoming_value
		nitem = frappe.get_doc("Item", order.production_item)
		sales_price = item_qty * nitem.standard_rate
		int_loss = 0
		profit = ((sales_price - act_cost - int_loss) * 100)/act_cost

		total_bom_rm_cost += bom_rm_cost
		total_bom_op_cost += bom_op_cost
		total_act_rm_cost += act_rm_cost
		total_act_op_cost += act_op_cost
		total_bom_cost += bom_cost
		total_act_cost += act_cost
		total_production += sales_price

		result.append([order.production_item, se.posting_date, se.name, bom_rm_cost, act_rm_cost, bom_op_cost, act_op_cost, bom_cost, act_cost, profit])

	total_profit = ((total_production - total_act_cost) * 100 / total_act_cost)
	result.append(["", "", "", "", "", "", "", "","",""])
	result.append(["Total", "", "", total_bom_rm_cost, total_act_rm_cost, total_bom_op_cost, total_act_op_cost, total_bom_cost, total_act_cost, total_profit])

	return result

def get_columns():
	columns = [
			_("Product Name") + ":Link/Item:150", _("Production Date") + ":Date:120", _("Stock Entry") + ":Link/Stock Entry:100",
			_("BOM Material Cost") + ":Float:100", _("Actual Material Cost") + ":Float:100",
			_("BOM Operation Cost") + ":Float:100", _("Actual Operation Cost") + ":Float:100",
			_("BOM Cost") + ":Float:100", _("Actual Cost") + ":Float:100",
			  _("Profit") + ":Float:100",
			]
	return columns

def get_op_cost_per_box(start_date, end_date):
	op_cost = get_total_expenses(start_date, end_date)
	(boxes, production) = get_production_details(start_date, end_date)
	return op_cost/boxes

def get_total_expenses(start_date, end_date):
	expenses = frappe.db.sql("""select name, total_debit
									from `tabJournal Entry`
									where voucher_type='Journal Entry' and posting_date between '{0}' and '{1}'"""\
									.format(start_date, end_date),as_dict=1)

	expense_total = 0

	for expense_entry in expenses:
		expense = frappe.get_doc("Journal Entry", expense_entry.name)
		#print("{0}    {1}".format(expense.title, expense.total_debit))
		expense_total += expense.total_debit

	return expense_total

def get_production_details(start_date, end_date):
	prod_orders = frappe.get_all("Production Order", fields={"status":"Completed"})
	total_boxes = total_production = 0

	for order_entry in prod_orders:
		order = frappe.get_doc("Production Order", order_entry.name)
		stock_entry = frappe.get_doc("Stock Entry", {"production_order":order.name})
		total_boxes += order.produced_qty
		total_production += stock_entry.total_outgoing_value

	return (total_boxes, total_production)
