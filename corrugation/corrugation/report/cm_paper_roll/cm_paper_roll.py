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
	columns = [
			_("Roll Name") + ":Link/CM Paper Roll:300",  _("Weight") + ":Float:70",	_("Colour") + ":Data:100",
			_("BF") + ":Float:70",  _("GSM") + ":Float:70", _("Deck") + ":Float:70",
			_("Supplier") + ":Data:100", _("Location") + ":Data:100", _("Status") + ":Data:100"
			]
	return columns
