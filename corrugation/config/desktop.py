# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"module_name": "Corrugation",
			"color": "green",
			"icon": "octicon octicon-package",
			"type": "module",
			"label": _("Corrugation")
		},
		{
			"module_name": "Corrugation Order",
			"_doctype": "CM Corrugation Order",
			"color": "brown",
			"icon": "octicon octicon-tools",
			"type": "link",
			"link": "List/CM Corrugation Order"
		},
		{
			"module_name": "Box Production Order",
			"_doctype": "CM Production Order",
			"color": "brown",
			"icon": "octicon octicon-tools",
			"type": "link",
			"link": "List/CM Production Order"
		},
		{
			"module_name": "Roll Entry",
			"_doctype": "CM Paper Roll Register",
			"color": "#f39c11",
			"icon": "octicon octicon-tools",
			"type": "link",
			"link": "List/CM Paper Roll Register"
		},
		{
			"module_name": "Rolls Report ",
			"_doctype": "CM Paper Roll",
			"color": "#f39c12",
			"icon": "octicon octicon-database",
			"type": "link",
			"link": "query-report/CM Paper Roll"
		},
		{
			"module_name": "Box Report ",
			"_doctype": "CM Box",
			"color": "#f39c12",
			"icon": "octicon octicon-package",
			"type": "link",
			"link": "query-report/CM Box Report"
		},
		{
			"module_name": "Stock Summary",
			"_doctype": "CM Box",
			"color": "#f39c12",
			"icon": "octicon octicon-package",
			"type": "link",
			"link": "query-report/CM Stock Report"
		},
		{
			"module_name": "Expense Entry",
			"_doctype": "Journal Entry",
			"color": "#f39c12",
			"icon": "octicon octicon-book",
			"type": "link",
			"link": "List/Journal Entry"
		},
		{
			"module_name": "Sales Invoice",
			"_doctype": "Sales Invoice",
			"color": "#f39c12",
			"icon": "octicon octicon-book",
			"type": "link",
			"link": "List/Sales Invoice"
		},
		{
			"module_name": "Purchase Receipt",
			"_doctype": "Purchase Receipt",
			"color": "#f39c12",
			"icon": "octicon octicon-book",
			"type": "link",
			"link": "List/Purchase Receipt"
		},
	]
