// Copyright (c) 2016, sathishpy@gmail.com and contributors
// For license information, please see license.txt
/* eslint-disable */
frappe.query_reports["CM Corrugation Report"] = {
	"filters": [
		{
						"fieldname":"from_date",
						"label": __("From Date"),
						"fieldtype": "Date",
						"default": frappe.datetime.add_days(frappe.datetime.get_today(), -7),
		},
		{
						"fieldname":"to_date",
						"label": __("To Date"),
						"fieldtype": "Date",
						"default": frappe.datetime.get_today(),
		},
	]
}
