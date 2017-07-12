# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class CMBox(Document):
	def get_item_doc(self):
		item = frappe.db.get_value("Item", filters={"item_code": self.box_code})
		if item == None:
			print "Creating item for box {0}".format(self.box_name)
			return frappe.new_doc("Item")
		else:
			return frappe.get_doc("Item", item)

	def get_item_descriptions(self):
		bom = frappe.db.get_value("CM Box Description", filters={"box": self.box_code})
		if bom == None:
			print "Creating BOM for box {0}".format(self.box_name)
			box =[frappe.new_doc("CM Box Description")]
			return box
		else:
			boxes = frappe.get_all("CM Box Description", filters={'box': self.box_code})
			box_docs = [frappe.get_doc("CM Box Description", box) for box in boxes]
			return box_docs

	def before_save(self):
		item = self.get_item_doc()
		item.item_name = self.box_name
		item.item_code = self.box_code
		item.standard_rate = self.box_rate
		item.item_group = "Products"
		item.default_warehouse = frappe.db.get_value("Warehouse", filters={"warehouse_name": _("Finished Goods")})
		item.save(ignore_permissions=True)
		self.box_item = item.name

	def on_update(self):
		item = frappe.get_doc("Item", self.box_item)
		for box_bom in self.get_item_descriptions():
			print "Updating box bom {0}".format(box_bom)
			box_bom.box = self.name
			box_bom.item = item.name
			box_bom.item_name = item.item_name
			box_bom.item_ply_count = self.box_ply_count
			box_bom.item_top_type = self.box_top_type
			box_bom.item_rate = self.box_rate
			if box_bom.item_length != self.box_length or box_bom.item_width != self.box_width or box_bom.item_height != self.box_height:
				box_bom.item_length = self.box_length
				box_bom.item_width = self.box_width
				box_bom.item_height = self.box_height
				box_bom.populate_raw_materials()
			box_bom.save(ignore_permissions=True)
