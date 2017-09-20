# Copyright (c) 2013, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.stock.dashboard.item_dashboard import get_data

def execute(filters=None):
	item_group = filters.get("item_group")
	columns, data = [], []
	items = get_data(None, None, item_group)
	columns = get_columns ()
	for item in items:
		if item.actual_qty == 0: continue
		lt = list()
		lt.append (item.warehouse)
		lt.append (item.item_code)
		lt.append (item.actual_qty)
		notes = ""
		if (item_group == "Paper"):
			rolls = frappe.db.sql("""select number, weight from `tabCM Paper Roll` where paper='{0}'""".format(item.item_code), as_dict=1)
			notes = ", ".join(roll.number + "(" + str(int(roll.weight)) + ")" for roll in rolls if roll.weight > 10)
		elif (item_group == "Board Layer"):
			orders = frappe.db.sql("""select name, stock_batch_qty from `tabCM Corrugation Order`
											where board_name='{0}' and stock_batch_qty > 0 and docstatus != 2""".format(item.item_code), as_dict=1)
			notes = ", ".join(order.name + "(" + str(order.stock_batch_qty) + ")" for order in orders)
		lt.append(notes)
		data.append (lt)
	return columns, data

def get_columns():
	columns = [
			_("Warehouse") + ":Link/Warehouse:150", _("Item") + ":Link/Item:250",  _("Quantity") + ":Float:100",
			_("Notes") + ":Data:1000"
			]
	return columns
