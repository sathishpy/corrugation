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
			"module_name": "CM Corrugation Order",
			"_doctype": "CM Corrugation Order",
			"color": "#f39c12",
			"icon": "octicon octicon-tools",
			"type": "link",
			"link": "List/CM Corrugation Order"
		},
		{
			"module_name": "CM Production Order",
			"_doctype": "CM Production Order",
			"color": "#f39c12",
			"icon": "octicon octicon-tools",
			"type": "link",
			"link": "List/CM Production Order"
		},
		{
			"module_name": "CM Paper Roll",
			"_doctype": "CM Paper Roll",
			"color": "#f39c12",
			"icon": "octicon octicon-tools",
			"type": "link",
			"link": "Report/CM Paper Roll"
		},

	]
