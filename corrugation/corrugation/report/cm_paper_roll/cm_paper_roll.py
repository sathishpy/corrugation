# Copyright (c) 2013, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import datetime
import calendar

def execute(filters=None):
	columns, data = [], []
	paper_rolls = frappe.db.sql("""select name, paper, weight, location, status from `tabCM Paper Roll` where weight > 0""",as_dict=1)
	columns = get_columns ()
	for roll in paper_rolls:
		print roll
		lt = list()
		lt.append (roll.name)
		lt.append (roll.weight)
		item = frappe.get_doc("Item", roll.paper)
		for attribute in item.attributes:
			lt.append(attribute.attribute_value)
			print ("{0} : {1}".format(attribute.attribute, attribute.attribute_value))
		lt.append (roll.location)
		lt.append (roll.status)
		data.append (lt)
	return columns, data

def get_columns():
        return [
                {
                    "fieldname": "name",
					"label"	   : "name",
                    "width": 250
                },
                {
                    "fieldname": "weight",
					"label"	   : "Weight",
                    "width": 60
                },
                {
                    "fieldname": "colour",
					"label"	   : "colour",
                    "width": 120
                },
                {
                    "fieldname": "bf",
					"label"	   : "BF",
                    "width": 90
                },
                {
                    "fieldname": "gsm",
					"label"	   : "GSM",
                    "width": 110
                },
                {
                    "fieldname": "deck",
					"label"	   : "Deck",
                    "width": 110
                },
                {
                    "fieldname": "supplier",
					"label"	   : "Supplier",
                    "width": 110
                },
                {
                    "fieldname": "location",
					"label"	   : "location",
                    "width": 100
                },
                {
                    "fieldname": "status",
					"label"	   : "Status",
                    "width": 60
                },
	       ]
