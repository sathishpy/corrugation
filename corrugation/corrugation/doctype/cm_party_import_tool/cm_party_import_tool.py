# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import xml.dom.minidom

class CMPartyImportTool(Document):
	def on_update(self):
		print("File is {0}".format(self.filename))
		dom = xml.dom.minidom.parse("/home/spoojary/factory-skpi/sites/myskpi.in" + self.filename)
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
			else:
				print "No tax ID for {0}".format(party_entry.party_name)
			addr_node = ledger.getElementsByTagName("ADDRESS.LIST")
			if (len(addr_node) > 0):
				party_entry.party_address = getText(addr_node[0])
			else:
				print "No address for {0}".format(party_entry.party_name)
			self.append("party_items", party_entry)


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
