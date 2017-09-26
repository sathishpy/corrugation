// Copyright (c) 2016, sathishpy@gmail.com and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["CM Production Report"] = {
	"filters": [
		{
						"fieldname":"period",
						"label": __("Period"),
						"fieldtype": "Int",
						"default": 4,
		},
		{
						"fieldname":"period_type",
						"label": __("Period Type"),
						"fieldtype": "Select",
						"options": "Days\nWeeks\nMonths\nYears",
						"default": "Weeks",
		},
	]
}
