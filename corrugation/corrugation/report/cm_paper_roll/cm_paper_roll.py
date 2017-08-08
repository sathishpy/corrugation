# Copyright (c) 2013, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import datetime
import calendar
from frappe import _

def execute(filters=None):
	columns, data = [], []
	paper_rolls = frappe.db.sql("""select number, paper, weight, location, status from `tabCM Paper Roll` where weight > 0""",as_dict=1)
	columns = get_columns ()
	for roll in paper_rolls:
		lt = list()
		lt.append (roll.number)
		lt.append (roll.paper)
		lt.append (roll.weight)
		item = frappe.get_doc("Item", roll.paper)
		for attribute in item.attributes:
			lt.append(attribute.attribute_value)
		lt.append (item.standard_rate)
		lt.append (item.valuation_rate)
		lt.append ("")
		data.append (lt)
	return columns, data

def get_columns():
	columns = [
			_("Roll No") + ":Int:70", _("Paper") + ":Link/Item:230",  _("Weight") + ":Float:70", _("Colour") + ":Data:100",
			_("BF") + ":Float:70",  _("GSM") + ":Float:70", _("Deck") + ":Float:70",
			_("Rate") + ":Currency:70", _("Landing Rate") + ":Currency:130", _("Supplier") + ":Data:100"
			]
	return columns
