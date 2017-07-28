# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from corrugation.corrugation.doctype.cm_box_description.cm_box_description import get_item_rate

class CMPaperRoll(Document):
	def autoname(self):
		roll_name = "{0}-RL-{1}".format(self.paper, self.number)
		rolls = frappe.db.sql_list("""select name from `tabCM Paper Roll` where name=%s""", roll_name)
		if rolls:
			roll_name = roll_name + ('-%.2i' % len(rolls))
		self.name = roll_name

	def get_unit_rate(self):
		roll_rate = self.unit_cost
		if (roll_rate == 0):
			roll_rate = get_item_rate(self.paper)
		return roll_rate
