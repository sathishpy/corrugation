from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Production"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "CM Production Order",
					"description": _("Orders released for production."),
                    "label": _("Production Order")
				},
				{
					"type": "doctype",
					"name": "CM Shared Production Order",
					"description": _("Shared Production Orders."),
                    "label": _("Shared Production Order")
				},
				{
					"type": "doctype",
					"name": "CM Box Description",
					"description": _("Bill of Materials (BOM)"),
					"label": _("Box Manufacturing Details")
				},
            ]
        },
        {
            "label": _("Stock"),
            "items": [
				{
					"type": "doctype",
					"name": "CM Paper Roll Register",
                    "label": _("Register Paper Rolls")
				},
				{
					"type": "doctype",
					"name": "CM Box",
                    "label": _("Register New Box")
				},
				{
					"type": "doctype",
					"name": "CM Paper",
                    "label": _("Register New Paper")
				},
			]
		},
		{
			"label": _("Sales and Purchase"),
			"items": [
				{
					"type": "doctype",
					"name": "Sales Order",
					"label": _("Sales Order"),
				},
				{
					"type": "doctype",
					"name": "Purchase Invoice",
					"label": _("Purchase Invoice"),
				},
				{
					"type": "doctype",
					"name": "Purchase Receipt",
					"label": _("Purchase Receipt"),
				},
			]
		},
		{
			"label": _("Reports"),
			"icon": "fa fa-list",
			"items": [
				{
					"type": "report",
                    "name": "CM Product Costs",
					"label": _("Production Cost Analysis"),
					"is_query_report": True,
				},
                {
                    "type": "report",
                    "name": "CM Paper Roll",
                    "label": _("Paper Rolls"),
					"is_query_report": True,
                }
			]
		},
		{
			"label": _("Tools"),
			"items": [
				{
					"type": "doctype",
                    "name": "CM Export Data",
					"label": _("Export Data"),
				},
				{
					"type": "doctype",
					"name": "CM Data Import Tool",
					"label": _("Import Master Data"),
				},
				{
					"type": "report",
                    "name": "CM Tally Export",
					"is_query_report": True,
				},
			]
		},
		{
			"label": _("Setup"),
			"items": [
				{
					"type": "doctype",
					"name": "Manufacturing Settings",
					"description": _("Global settings for all manufacturing processes."),
				},
			]
		},
	]
