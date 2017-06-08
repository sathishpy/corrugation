# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class CMProductionOrder(Document):
	def populate_box_rolls(self):
		box_details = frappe.get_doc("CM Box Description", self.cm_box_detail)
		self.cm_box_rolls = []
		for paper in box_details.item_papers:
			print "Paper {0}".format(paper.rm)
			roll = get_smallest_roll(paper.rm)
			if roll is None:
				print("Failed to find a roll for paper {0}".format(paper.rm))
				continue
			roll.cm_status = "In Use"
			roll.save()
			roll_item = frappe.new_doc("CM Box Roll Detail")
			roll_item.cm_paper = roll.name
			roll_item.cm_start_weight = roll.cm_weight
			print ("Adding {0}".format(roll_item))
			self.append("cm_box_rolls", roll_item)

def is_paper_item(rm):
	if "paper" in rm.item_name or "Paper" in rm.item_name:
		return True
	return False

def get_smallest_roll(paper):
	rolls = frappe.get_all("CM Paper Roll", fields={"cm_item" : paper})
	weight = 10000
	small_roll = None
	for p_roll in rolls:
		roll = frappe.get_doc("CM Paper Roll", p_roll.name)
		print "Roll is {0} Weight {1}".format(roll.name, roll.cm_weight)
		if (roll.cm_status == "Ready" and roll.cm_weight < weight):
			small_roll = roll
			weight = roll.cm_weight
	return small_roll
