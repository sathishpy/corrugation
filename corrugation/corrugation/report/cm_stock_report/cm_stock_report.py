# Copyright (c) 2013, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.stock.dashboard.item_dashboard import get_data

def execute(filters=None):
	item_groups = [filters.get("group_name")]
	if ("Board Detail" in item_groups):
		return execute_board_detail(filters)

	if (filters.get("group_name") == "Others"):
		item_groups = ["Gum", "Ink"]
	columns, data, items = [], [], []
	for item_group in item_groups:
		items += get_data(None, None, item_group)
	if (filters.get("group_name") == "Products"):
		columns = get_detailed_production_columns()
	else:
		columns = get_columns ()
	for item in items:
		if item.actual_qty == 0: continue
		lt = list()
		lt.append (item.item_code)
		lt.append (item.actual_qty)
		lt.append (item.warehouse)
		notes = ""
		if (item_group == "Paper"):
			rolls = frappe.db.sql("""select number, weight from `tabCM Paper Roll` where paper='{0}'""".format(item.item_code), as_dict=1)
			notes = ", ".join(roll.number + "(" + str(int(roll.weight)) + ")" for roll in rolls if roll.weight > 10)
		elif (item_group == "Board Layer"):
			orders = frappe.db.sql("""select name, stock_batch_qty from `tabCM Corrugation Order`
											where board_name='{0}' and stock_batch_qty > 0 and docstatus != 2""".format(item.item_code), as_dict=1)
			notes = ", ".join(order.name + "(" + str(order.stock_batch_qty) + ")" for order in orders)
		elif (item_group == "Products"):
			orders = frappe.db.sql("""select name from `tabCM Corrugation Order`
											where box ='{0}' and stock_qty > 0 """.format(item.item_code), as_dict=1)
			production_order = ", ".join(order.name  for order in orders)	
			lt.append(production_order)
		if (item_group !="Products"):	
			lt.append(notes)
		data.append (lt)
	return columns, data

def execute_board_detail(filters=None):
	columns = get_detailed_corrugation_columns()
	items = get_data(None, None, "Board Layer")
	data = []
	for item in items:
		if item.actual_qty == 0: continue
		orders = frappe.db.sql("""select mfg_date, name, stock_batch_qty from `tabCM Corrugation Order`
										where board_name='{0}' and stock_batch_qty > 0 and docstatus != 2""".format(item.item_code), as_dict=1)
		for order in orders:
			if (order.stock_batch_qty == 0): continue
			lt = list()
			lt.append(order.mfg_date)
			lt.append (item.item_code)
			lt.append (order.stock_batch_qty)
			lt.append(order.name)
			data.append (lt)
	print("Returning data")
	return columns, data

def get_columns():
	columns = [
			_("Item") + ":Link/Item:250",  _("Quantity") + ":Float:100", _("Warehouse") + ":Link/Warehouse:150",
			_("Notes") + ":Data:1000"
			]
	return columns

def get_detailed_production_columns():
	columns = [
			_("Item") + ":Link/Item:250",  _("Quantity") + ":Float:100", _("Warehouse") + ":Link/Warehouse:150",
			_("Production order") + ":Link/CM Production Order:300"
			]
	return columns

def get_detailed_corrugation_columns():
	columns = [
			_("Date") + ":Date:200", _("Item") + ":Link/Item:250",  _("Quantity") + ":Float:100",
			_("Corrugation Order") + ":Link/CM Corrugation Order:400"
			]
	return columns
