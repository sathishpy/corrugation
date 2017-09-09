// Copyright (c) 2016, sathishpy@gmail.com and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["CM Stock Report"] = {
	"filters": [
		{
						"fieldname":"item_group",
						"label": __("Item Group"),
						"fieldtype": "Link",
						"options": "Item Group",
						"default": "Products",
		},
	]
}
