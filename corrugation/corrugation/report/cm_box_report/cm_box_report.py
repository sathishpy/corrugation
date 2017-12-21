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
		if (desc is None):
			print("No description present for box {0}".format(box.name))
			continue
		box_desc = frappe.get_doc("CM Box Description", desc)
		lt.append(box_desc.sheet_length)
		lt.append(box_desc.sheet_width)
		lt.append(box.box_rate)
		lt.append(box_desc.item_profit)
		lt.append(next((paper_item.rm for paper_item in box_desc.item_papers if paper_item.rm_type == "Top"), None))
		lt.append(next((paper_item.rm for paper_item in box_desc.item_papers if paper_item.rm_type == "Flute"), None))
		lt.append(desc)
		data.append (lt)
	return columns, data

def get_columns():
	columns = [
			_("Box") + ":Link/CM Box:150", _("Length") + ":Float:60", _("Width") + ":Float:60", _("Height") + ":Float:60",
			_("Layers") + ":Int:50", _("Sheet Length") + ":Float:60", _("Deck") + ":Float:60",
			_("Rate") + ":Currency:60", _("Proft %") + ":Float:60", _("Top") + ":Link/Item:150", _("Board") + ":Link/Item:150", _("Description") + ":Link/CM Box Description:150"
			]
	return columns
