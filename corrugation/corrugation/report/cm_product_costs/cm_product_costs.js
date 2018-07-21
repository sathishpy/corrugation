// Copyright (c) 2016, sathishpy@gmail.com and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["CM Product Costs"] = {
	"filters": [
		{
						"fieldname":"from_date",
						"label": __("From Date"),
						"fieldtype": "Date",
						"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
						"fieldname":"to_date",
						"label": __("To Date"),
						"fieldtype": "Date",
						"default": frappe.datetime.get_today(),
<<<<<<< HEAD
		},
		{
						"fieldname":"consolidated",
						"label": __("Consolidated"),
						"fieldtype": "Check",
						"default": 1,
		},
=======
		}
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
	]
}
