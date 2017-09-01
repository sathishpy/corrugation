# Copyright (c) 2013, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns, data = [], []
	box_list = frappe.db.sql("""select name, box_length, box_width, box_height, box_ply_count, box_rate from `tabCM Box`""",as_dict=1)
	columns = get_columns ()
	for box in box_list:
		lt = list()
		lt.append (box.name)
		lt.append (box.box_length)
		lt.append (box.box_width)
		lt.append (box.box_height)
		lt.append (box.box_ply_count)
		desc = frappe.db.get_value("CM Box Description", filters={"box": box.name})
		box_desc = frappe.get_doc("CM Box Description", desc)
		lt.append(box_desc.sheet_length)
		lt.append(box_desc.sheet_width)
		lt.append(box.box_rate)
		lt.append(box_desc.item_profit)
		lt.append(next((paper_item.rm for paper_item in box_desc.item_papers if paper_item.rm_type == "Top"), None))
		lt.append(next((paper_item.rm for paper_item in box_desc.item_papers if paper_item.rm_type == "Flute"), None))
		data.append (lt)
	return columns, data

def get_columns():
	columns = [
			_("Box") + ":Link/CM Box:150", _("Length") + ":Float:70", _("Width") + ":Float:70", _("Height") + ":Float:70",
			_("Layer") + ":Float:70", _("Sheet Length") + ":Float:70", _("Deck") + ":Float:70",
			_("Rate") + ":Currency:70", _("Proft %") + ":Float:70", _("Top") + ":Link/Item:170", _("Board") + ":Link/Item:170"
			]
	return columns
