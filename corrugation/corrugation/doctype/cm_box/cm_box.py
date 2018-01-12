# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from corrugation.corrugation.utils import delete_submitted_document

class CMBox(Document):
	def autoname(self):
		self.name = self.box_code
		self.box_item = None

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

	def validate(self):
		if ("Plate" in self.box_type and self.box_height != 0):
			frappe.throw("Height should be zero for plate items")
		if ("Plate" not in self.box_type and self.box_height == 0):
			frappe.throw("Height should be zero only for plate items")
		if self.box_item is not None and self.name != self.box_item:
			print("Renaming {0} to {1}".format(self.box_item, self.name))
			frappe.rename_doc("Item", self.box_item, self.name)

	def before_save(self):
		item = self.get_item_doc()
		item.item_name = self.box_name
		item.item_code = self.box_code
		item.standard_rate = self.box_rate
		item.item_group = "Products"
		item.is_purchase_item = False
		item.gst_hsn_code = "4819"
		item.default_warehouse = frappe.db.get_value("Warehouse", filters={"warehouse_name": _("Finished Goods")})
		if (self.box_type == "Top Plate"):
			item.stock_uom = "Kg"
			self.box_ply_count = 1
		item.save()
		self.box_item = item.name

		item_price = frappe.db.get_value("Item Price", filters={"item_code": self.box_code, "price_list": "Standard Selling"})
		if (not item_price):
			price_doc = frappe.new_doc("Item Price")
			price_doc.update({"price_list": "Standard Selling", "selling": True, "item_code": self.box_code, "price_list_rate": self.box_rate})
			price_doc.save()
		else:
			frappe.db.set_value("Item Price", item_price, "price_list_rate", self.box_rate)

	def on_update(self):
		item = frappe.get_doc("Item", self.box_item)
		for box_bom in self.get_item_descriptions():
			if (box_bom.docstatus == 1):
				box_bom.update_cost_after_submit()
				continue
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
			print "Updated box bom {0}".format(box_bom.name)

	def on_trash(self):
		box_descs = frappe.get_all("CM Box Description", filters={'box': self.box_code})
		for box_desc in box_descs:
			delete_submitted_document("CM Box Description", box_desc)

		boms = frappe.get_all("BOM", filters={'item': self.box_item})
		for bom in boms:
			delete_submitted_document("BOM", bom)

		price_lists = frappe.get_all("Item Price", filters={"item_code": self.box_code})
		for item_price in price_lists:
			price_doc = frappe.get_doc("Item Price", item_price)
			price_doc.delete()

		try:
			item = frappe.get_doc("Item", self.box_code)
			item.delete()
		except:
			frappe.msgprint("Failed to delete the associated item")
