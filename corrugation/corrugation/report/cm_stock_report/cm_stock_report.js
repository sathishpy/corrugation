// Copyright (c) 2016, sathishpy@gmail.com and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["CM Stock Report"] = {
	"filters": [
		{
						"fieldname":"group_name",
						"label": __("Item Group"),
						"fieldtype": "Select",
						"options": "Products\nPaper\nBoard Layer\nOthers",
						"default": "Products",
		},
	]
}
