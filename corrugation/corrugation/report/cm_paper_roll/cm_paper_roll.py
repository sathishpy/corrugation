# Copyright (c) 2013, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import datetime
import calendar

def execute(filters=None):
	columns, data = [], []
	cm_paper_roll = frappe.db.sql("""select name, cm_weight, cm_location, cm_status, cm_item  from `tabCM Paper Roll`""",as_dict=1)
	columns = get_columns ()
	for en in cm_paper_roll:
		print en
		l = ()
		lt = list (l)
		lt.append (en.name)
		lt.append (en.cm_weight)
		lt.append (en.cm_location)
		lt.append (en.cm_status)
		#lt.append (en.cm_item)
		cm_item = frappe.db.sql("""select valuation_rate, standard_rate, weightage from `tabItem` where name = %s """,en.cm_item)
		for it_en in cm_item:
			print it_en
			for it in it_en:
				lt.append (it)
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
                        "fieldname": "location",
			"label"	   : "location",
                        "width": 100
                },
                {
                        "fieldname": "status",
			"label"	   : "Status",
                        "width": 60 
                },
                {
                        "fieldname": "valuation_rate",
			"label"	   : "Valuation Rate",
                        "width": 120
                },
                {
                        "fieldname": "standard_rate",
			"label"	   : "Standard Rate",
                        "width": 90
                },
                {
                        "fieldname": "weightage",
			"label"	   : "Weightage",
                        "width": 110
                }
	       ]
