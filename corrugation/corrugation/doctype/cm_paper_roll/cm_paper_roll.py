# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from corrugation.corrugation.doctype.cm_box_description.cm_box_description import get_item_rate

class CMPaperRoll(Document):
	def autoname(self):
		self.name = "{0}-RL-{1}".format(self.paper, self.number)

	def get_unit_rate(self, exclude_tax=True):
		roll_rate = self.basic_cost + self.misc_cost
		if (roll_rate == 0):
			roll_rate = get_item_rate(self.paper, exclude_tax)
		return roll_rate
