# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import xml.dom.minidom
import csv
from frappe import _
from erpnext.controllers.item_variant import create_variant, find_variant
class CMDataImportTool(Document):
	def autoname(self):
		self.name = self.data_type + "-exported-data"

	def on_update(self):
		if self.filename is None: return
		filename = self.filename.split("/")[-1]
		filepath = frappe.get_site_path('private', 'files', filename)
		if (self.data_type == "Party"):
			self.extract_party_details(filepath)
		elif self.data_type == "Roll":
			self.extract_roll_details(filepath)
		elif self.data_type == "Box":
			self.extract_box_details(filepath)

	def export_data(self):
		if self.filename is None: return
		if (self.data_type == "Party"):
			self.export_parties()
		elif self.data_type == "Roll":
			self.export_rolls()
		elif self.data_type == "Box":
			self.export_boxes()

	def extract_party_details(self, filepath):
		print("File is {0}".format(filepath))
		dom = xml.dom.minidom.parse(filepath)
		self.party_items = []
		ledger_entries = dom.getElementsByTagName("LEDGER")
		for ledger in ledger_entries:
			parent = ledger.getElementsByTagName("PARENT")[0]
			parent_type = getText(parent)
			if "Sundry" not in parent_type: continue
			party_entry = frappe.new_doc("CM Import Party Item")
			party_entry.party_name = ledger.getAttribute("NAME")
			party_entry.party_type = parent_type
			tax_node = ledger.getElementsByTagName("SALESTAXNUMBER")
			if len(tax_node) != 1:
				tax_node = ledger.getElementsByTagName("INCOMETAXNUMBER")

			if len(tax_node) == 1:
				party_entry.party_tin = getText(tax_node[0])
			addr_node = ledger.getElementsByTagName("ADDRESS.LIST")
			if (len(addr_node) > 0):
				party_entry.party_address = getText(addr_node[0])
			self.append("party_items", party_entry)

	def export_parties(self):
		entries = 0
		for party in self.party_items:
			if party.party_type != "Sundry Debtors" and party.party_type != "Sundry Creditors": continue
			print "Inserting {0} - {1}".format(party.party_type, party.party_name)
			if (party.party_type == "Sundry Debtors"):
				party_entry = frappe.new_doc("Customer")
				party_entry.customer_name = party.party_name
				party_entry.customer_type = "Company"
				party_entry.customer_group = "Commercial"
				party_entry.territory = "India"
				party_entry.tax_id = party.party_tin
				party_entry.insert()
			else:
				party_entry = frappe.new_doc("Supplier")
				party_entry.supplier_name = party.party_name
				party_entry.supplier_type = "Local"
				party_entry.tax_id = party.party_tin
				party_entry.insert()
			self.add_party_address(party)

	def add_party_address(self, party):
		if (party.party_address is None): return
		addr_list = party.party_address.splitlines(True)
		addr_size = len(addr_list)
		if (addr_size < 1): return

		address = frappe.new_doc("Address")
		address.address_title = party.party_name
		address.address_type = "Billing"

		last_line = str(addr_list[addr_size-1].strip().rstrip(',').rstrip('.'))
		pincode = filter(str.isdigit, last_line)
		last_line = last_line.strip(pincode)
		address.city = last_line
		address.pincode = pincode

		address.address_line1 = addr_list[0].strip().rstrip(',')
		if (addr_size > 2):
			address.address_line2 = addr_list[1].strip().rstrip(',')

		link  = frappe.new_doc("Dynamic Link")
		if (party.party_type == "Sundry Debtors"):
			link.link_doctype = "Customer"
		else:
			link.link_doctype = "Supplier"
		link.link_name = party.party_name
		address.append("links", link)
		address.insert()

		#print("Addres {0}, {1}, {2} {3}".format(address.address_line1, address.address_line2, address.city, pincode ))
	def extract_roll_details(self, filepath):
		self.party_items = []
		self.roll_items = []
		with open(filepath) as csvfile:
			rolls = csv.DictReader(csvfile)
			for roll in rolls:
				roll_item = frappe.new_doc("CM Import Roll Item")
				roll_item.paper_color = roll["Color"]
				roll_item.paper_bf = roll["BF"]
				roll_item.paper_gsm = roll["GSM"]
				roll_item.paper_deck = roll["Deck"]
				roll_item.roll_weight = roll["Weight"]
				self.append("roll_items", roll_item)

	def export_rolls(self):
		for roll in self.roll_items:
			variant_args = {"Colour": roll.paper_color, "BF": roll.paper_bf, "GSM": roll.paper_gsm, "Deck": roll.paper_deck}
			paper = find_variant("Paper-RM", variant_args)
			if (paper == None):
				print ("Creating Paper for args {0}".format(variant_args))
				paper_doc = create_variant("Paper-RM", variant_args)
				if (paper_doc != None):
					paper_doc.save(ignore_permissions=True)
					paper = paper_doc.name
			else:
				print("Found paper {0}".format(paper))

			if (paper == None):
				frappe.throw("Failed to create the paper variant")
				continue

			paper_roll = frappe.new_doc("CM Paper Roll")
			paper_roll.paper = paper
			paper_roll.weight = roll.roll_weight
			paper_roll.status = "Ready"
			paper_roll.insert()

	def extract_box_details(self, filepath):
		self.party_items = []
		self.roll_items = []
		self.box_items = []
		with open(filepath) as csvfile:
			boxes = csv.DictReader(csvfile)
			for box in boxes:
				box_item = frappe.new_doc("CM Import Box Item")
				box_item.box_name = box["Name"]
				box_item.box_code = box["Code"]
				box_item.length = box["Length"]
				box_item.width = box["Width"]
				box_item.height = box["Height"]
				box_item.ply = box["Ply"]
				box_item.rate = box["Rate"]
				self.append("box_items", box_item)

	def export_boxes(self):
		for box_item in self.box_items:
			item = frappe.new_doc("Item")
			item.item_name = box_item.box_name
			if (box_item.box_code):
				item.item_code = box_item.box_code
			else:
				item.item_code = box_item.box_name
			item.standard_rate = box_item.rate
			item.item_group = "Products"
			item.default_warehouse = frappe.db.get_value("Warehouse", filters={"warehouse_name": _("Finished Goods")})
			print "Exporting box {0}-{1}.".format(item.item_name, item.item_code)
			item.save(ignore_permissions=True)

			box = frappe.new_doc("CM Box Description")
			box.item = item.name
			box.item_length = box_item.length
			box.item_width = box_item.width
			box.item_height = box_item.height
			box.item_ply_count = box_item.ply
			box.save(ignore_permissions=True)

def getText(node):
	text = []
	children = node.childNodes
	for child in children:
		if child.nodeType == node.TEXT_NODE and child.data != None:
			text.append(child.data)
		else:
			gchilds = child.childNodes
			for gchild in gchilds:
				if gchild.nodeType == node.TEXT_NODE and gchild.data != None:
					text.append(gchild.data)
	print "Text is {0}".format(''.join(text))
	return ''.join(text).strip()
