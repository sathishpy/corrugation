# Copyright (c) 2013, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate
import datetime
import calendar

def execute(filters=None):
	columns, data = get_columns(filter), []
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	query = """select mfg_date, name, box, mfg_qty from `tabCM Corrugation Order`
				where mfg_date between '{0}' and '{1}'
				order by mfg_date""".format(from_date, to_date)
	entries = frappe.db.sql(query, as_dict=True)
	for entry in entries:
		crg_entry = [entry.mfg_date, entry.box, "", "", "", "", "", "", entry.mfg_qty, entry.name]
		crg_order = frappe.get_doc("CM Corrugation Order", entry.name)
		for roll_item in crg_order.paper_rolls:
			roll = frappe.get_doc("CM Paper Roll", roll_item.paper_roll)
			crg_entry[2], crg_entry[3], crg_entry[4] = roll_item.rm_type, roll.number, roll.paper
			crg_entry[5], crg_entry[6], crg_entry[7] = roll_item.start_weight, roll_item.final_weight, (roll_item.start_weight - roll_item.final_weight)
			data.append(crg_entry)
			crg_entry = ["", "", "", "", "", "", "", "", "",""]
	return columns, data

def get_columns(filter):
	columns = [
			_("Date") + ":Data:100", _("Box") + ":Link/CM Box:200", _("Layer") + ":Data:70",  _("Roll") + ":Int:70",  _("Paper") + ":Item:150",
			_("Start(Kg)") + ":Int:60",  _("Final(Kg))") + ":Int:60",  _("Used(Kg)") + ":Int:60",
			_("Board Count") + ":Data:80", _("Order ID") + ":Link/CM Corrugation Order:200"
			]
	return columns
