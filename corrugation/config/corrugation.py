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
<<<<<<< HEAD
					"name": "CM Corrugation Order",
                    "label": _("Corrugation Order")
				},
				{
					"type": "doctype",
=======
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
					"name": "CM Production Order",
					"description": _("Orders released for production."),
                    "label": _("Production Order")
				},
				{
					"type": "doctype",
<<<<<<< HEAD
					"name": "CM Shared Corrugation Order",
					"description": _("Shared Corrugation Orders."),
                    "label": _("Shared Corrugation Order")
=======
					"name": "CM Shared Production Order",
					"description": _("Shared Production Orders."),
                    "label": _("Shared Production Order")
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
				},
            ]
        },
        {
<<<<<<< HEAD
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
=======
            "label": _("Stock"),
            "items": [
				{
					"type": "doctype",
					"name": "CM Paper Roll Register",
                    "label": _("Register Paper Rolls")
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
			"label": _("Bill of Materials"),
			"items": [
				{
					"type": "doctype",
					"name": "CM Box Description",
					"description": _("Bill of Materials (BOM)"),
					"label": _("Box Description")
				},
				{
					"type": "doctype",
					"name": "BOM",
					"icon": "fa fa-sitemap",
					"label": _("BOM Browser"),
					"description": _("Tree of Bill of Materials"),
					"link": "Tree/BOM",
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
				},
			]
		},
		{
			"label": _("Reports"),
			"icon": "fa fa-list",
			"items": [
<<<<<<< HEAD
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
					"type": "report",
                    "name": "CM Stock Report",
					"label": _("Stock Summary"),
					"is_query_report": True,
				},
				{
					"type": "report",
                    "name": "CM Production Report",
					"label": _("Production Analysis"),
					"is_query_report": True,
				},
				{
					"type": "report",
                    "name": "CM Product Costs",
					"label": _("Production Cost Analysis"),
=======
				{
					"type": "report",
                    "name": "CM Product Costs",
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
					"is_query_report": True,
				},
				{
					"type": "report",
<<<<<<< HEAD
                    "name": "CM Corrugation Report",
					"label": _("Corrugation Job Report"),
=======
                    "name": "CM Tally Export",
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
					"is_query_report": True,
				},
			]
		},
		{
			"label": _("Tools"),
			"items": [
				{
					"type": "doctype",
<<<<<<< HEAD
					"name": "CM Payment Manager",
					"label": _("Payment Management"),
				},
				{
					"type": "doctype",
					"name": "CM Paper Management",
					"label": _("Paper Management"),
				},
				{
					"type": "doctype",
					"name": "CM Box Management",
					"label": _("Box Management"),
				},
				{
					"type": "doctype",
                    "name": "CM Export Data",
					"label": _("Export Data"),
				},
				{
					"type": "doctype",
					"name": "CM Data Import Tool",
					"label": _("Import Data"),
=======
                    "name": "CM Export Data",
					"label": _("Data Export to Tally"),
				},
				{
					"type": "doctype",
					"name": "CM Party Import Tool",
					"label": _("Import Master From Tally"),
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
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
