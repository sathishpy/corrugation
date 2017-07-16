# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

@frappe.whitelist()
def select_rolls_for_box(paper_items):
	added_rolls, available_rolls = [], []
	#build the unique list
	papers = [pi.rm for pi in paper_items]
	papers = list(set(papers))

	for paper_name in papers:
		rolls = frappe.get_all("CM Paper Roll", fields={"paper" : paper_name})
		available_rolls += rolls
		#print("Found {0} rolls for paper {1}".format(len(rolls), paper_name))

	for paper in paper_items:
		planned_qty = paper.rm_weight
		print "{0} Paper {1} needed: {2}".format(paper.rm_type, paper.rm, planned_qty)
		# Select all the rolls needed to manufacture required quantity
		while planned_qty > 0:
			roll = get_suitable_roll(paper.rm, paper.rm_type, planned_qty, added_rolls, available_rolls)

			if roll is None:
				frappe.throw("Failed to find a roll of weight {0} for paper {1}".format(planned_qty, paper.rm))
				break
			print "Selected Roll is {0} Weight {1}".format(roll.name, roll.weight)

			roll_item = frappe.new_doc("CM Production Roll Detail")
			roll_item.rm_type = paper.rm_type
			roll_item.paper_roll = roll.name
			roll_item.start_weight = roll.weight

			if (roll.weight > planned_qty):
				roll_item.est_final_weight = roll.weight - planned_qty
				planned_qty = 0
			else:
				roll_item.est_final_weight = 0
				planned_qty -= roll.weight

			roll_item.final_weight = roll_item.est_final_weight
			added_rolls += [roll_item]
			available_rolls = [rl for rl in available_rolls if rl.name != roll.name]
	return added_rolls

def get_smallest_roll(paper, rolls):
	weight = 100000
	small_roll = None
	for p_roll in rolls:
		roll = frappe.get_doc("CM Paper Roll", p_roll.name)
		if (roll.status != "Ready" or roll.paper != paper): continue
		if (roll.weight < weight and roll.weight > 10):
			small_roll = roll
			weight = roll.weight
	return small_roll

def get_roll_matching_weight(paper, weight, available_rolls):
	difference = 100000
	matching_roll = None
	for p_roll in available_rolls:
		roll = frappe.get_doc("CM Paper Roll", p_roll.name)
		if (roll.status != "Ready" or roll.paper != paper or roll.weight <= 10): continue
		weight_difference = (roll.weight - weight)
		if (weight_difference < difference or difference < 0):
			matching_roll = roll
			difference = weight_difference
	return matching_roll

def get_suitable_roll(paper, paper_type, weight, added_rolls, available_rolls):
	roll = get_prod_used_roll(added_rolls, paper, paper_type)
	if roll != None: return roll
	if (paper_type != "Top"):
		roll = get_roll_matching_weight(paper, weight, available_rolls)
	else:
		roll = get_smallest_roll(paper, available_rolls)
	return roll

def get_prod_used_roll(rolls, paper, rm_type):
	reuse_roll = None
	for p_roll in rolls:
		roll = frappe.get_doc("CM Paper Roll", p_roll.paper_roll)
		if roll.paper != paper: continue
		#Flute and bottom paper used simultaneosuly, so can't be shared
		sharing_conflict = False
		if (p_roll.rm_type == "Flute" and rm_type == "Liner"): sharing_conflict = True
		# Handle duplicate entries of shared rolls
		if (sharing_conflict):
			if (reuse_roll != None and reuse_roll.name == roll.name):
				reuse_roll = None
			continue

	 	print("Found roll {0} of weight {1} for {2}".format(p_roll.paper_roll, p_roll.est_final_weight, rm_type))
		if (reuse_roll != None and reuse_roll.name == roll.name):
			if p_roll.est_final_weight < 10:
				reuse_roll = None
				continue
		if p_roll.est_final_weight > 10:
			reuse_roll = roll
			reuse_roll.weight = p_roll.est_final_weight
	# Update the weight, but don't save it
	return reuse_roll
