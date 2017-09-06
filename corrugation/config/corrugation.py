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
					"name": "CM Corrugation Order",
                    "label": _("Corrugation Order")
				},
				{
					"type": "doctype",
					"name": "CM Production Order",
					"description": _("Orders released for production."),
                    "label": _("Production Order")
				},
				{
					"type": "doctype",
					"name": "CM Shared Corrugation Order",
					"description": _("Shared Corrugation Orders."),
                    "label": _("Shared Corrugation Order")
				},
            ]
        },
        {
            "label": _("Configuration"),
            "items": [
				{
					"type": "doctype",
					"name": "CM Box Description",
					"description": _("Bill of Materials (BOM)"),
					"label": _("Box Production Details")
				},
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
					"name": "Purchase Order",
					"label": _("Purchase Order"),
				},
				{
					"type": "doctype",
					"name": "Sales Invoice",
					"label": _("Sales Invoice"),
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
                    "name": "CM Box Report",
                    "label": _("Box List"),
					"is_query_report": True,
                },
                {
                    "type": "report",
                    "name": "CM Paper Roll",
                    "label": _("Paper Rolls"),
					"is_query_report": True,
                },
				{
					"type": "page",
					"name": "stock-balance",
					"label": _("Stock Summary")
				},
				{
					"type": "report",
                    "name": "CM Product Costs",
					"label": _("Production Cost Analysis"),
					"is_query_report": True,
				},
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
					"label": _("Import Data"),
				},
				{
					"type": "doctype",
					"name": "CM Box Management",
					"label": _("Box Management"),
				},
				{
					"type": "doctype",
					"name": "CM Paper Management",
					"label": _("Paper Management"),
				},
				{
					"type": "doctype",
					"name": "CM ESugama",
					"label": _("E-Sugama"),
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
