# Copyright (c) 2013, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import datetime
from frappe import _
from frappe.utils import nowdate
from datetime import date
from datetime import timedelta
from dateutil.relativedelta import relativedelta

def execute(filters=None):
	period = filters.get("period")
	period_type = filters.get("period_type")
	to_date = date.today()
	columns, data = get_columns(filter), []

	for idx in range(0, period):
		if (period_type == "Days"):
			from_date = to_date - timedelta(days=1)
		elif (period_type == "Weeks"):
			from_date = to_date - timedelta(days=7)
		elif (period_type == "Months"):
			if (to_date.day == 1):
				from_date = to_date - relativedelta(months=1)
			else:
				from_date = to_date.replace(day=1)
		else:
			if (to_date.month == 4):
				from_date = to_date - relativedelta(years=1)
			else:
				from_date = to_date.replace(month=4).replace(day=1)

		query = """select se.posting_date as date, en.item_code as item_code, en.qty as qty
									from `tabStock Entry` se
									LEFT JOIN `tabStock Entry Detail` en on en.parent=se.name
									where se.posting_date between '{0}' and '{1}'
									order by posting_date""".format(from_date.strftime('%Y-%m-%d'), to_date.strftime('%Y-%m-%d'))
		entries = frappe.db.sql(query, as_dict=True)
		#print "Running query {0} gave {1} items".format(query, len(entries))
		to_date = from_date
		paper_qty = box_qty = box_weight = box_cost = 0
		for entry in entries:
			group = frappe.db.get_value("Item", entry.item_code, "item_group")
			if (group == "Paper"):
				paper_qty += entry.qty
			elif (group == "Products"):
				box_qty += entry.qty
				box_desc_list = frappe.db.get_all("CM Box Description", filters={"item": entry.item_code})
				if (len(box_desc_list) > 0):
					box_weight += entry.qty * frappe.db.get_value("CM Box Description", box_desc_list[0].name, "item_weight")
				else:
					print("No decsription found ofr box {0}".format(entry.item_code))
				box_cost += entry.qty * frappe.db.get_value("Item", entry.item_code, "standard_rate")

		#print ("Adding {0} {1} {2}".format(paper_qty, box_qty, box_cost))
		data.append([from_date, paper_qty, box_qty, box_weight, box_cost])
	chart = get_chart_data(columns, data)
	data.append(["", "", "", "", ""])
	return columns, data, None, chart

def get_columns(filter):
	columns = [
			_("Date") + ":Data:200", _("Corrugated Paper") + ":Float:200", _("Box Production(Qty)") + ":Float:200",  _("Box Production(Weight)") + ":Float:200",
			_("Box Production(Amount)") + ":Float:200",
			]
	return columns

def get_chart_data(columns, data):
	data.reverse()
	x_intervals = ['x'] + [d[0] for d in data]

	paper_qty, box_qty, box_weight = [], [], []

	for d in data:
		paper_qty.append(d[1])
		box_qty.append(d[2])
		box_weight.append(d[3])

	columns = [x_intervals]
	columns.append(["Paper"] + paper_qty)
	columns.append(["Box"] + box_qty)
	columns.append(["BoxWeight "] + box_weight)

	chart = {
		"data": {
			'x': 'x',
			'columns': columns,
			'colors': {
				'Paper': 'Brown',
				'Box': 'Blue',
				'BoxWeight': 'Green'
			}
		}
	}

	chart["chart_type"] = "line"

	return chart
