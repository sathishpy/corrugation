# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import xml.dom.minidom

class CMPartyImportTool(Document):
	def autoname(self):
		self.name = "exported-data"

	def on_update(self):
		filename = self.filename.split("/")[-1]
		filepath = frappe.get_site_path('private', 'files', filename)
		print("File is {0}".format(filepath))
		dom = xml.dom.minidom.parse(filepath)
		self.party_items = []
		ledger_entries = dom.getElementsByTagName("LEDGER")
		for ledger in ledger_entries:
			parent = ledger.getElementsByTagName("PARENT")[0]
			parent_type = getText(parent)
			if "Sundry" not in parent_type: continue
			party_entry = frappe.new_doc("CM Party Item")
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
