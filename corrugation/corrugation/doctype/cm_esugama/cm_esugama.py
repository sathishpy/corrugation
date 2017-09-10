# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import xml.dom.minidom
from xml.dom.minidom import parseString
from datetime import datetime

class CMESugama(Document):
	def autoname(self):
		self.name = "ES-" + self.sales_invoice

	def create_esugam_xml(self):
		inv = frappe.get_doc("Sales Invoice", self.sales_invoice)
		qty = 0
		for item in inv.items:
			qty += item.qty
		posting_date = inv.posting_date.strftime('%d-%m-%Y')
		xml_data = """
	                <VAT505_req>
	                    <Vat505_Det>
	                        <Tin>{sender_tin}</Tin>
	                        <InvNo>{inv_no}</InvNo>
	                        <InvDt>{date}</InvDt>
	                        <Dn_dt>{date}</Dn_dt>
	                        <Buy_Tin>{cust_tin}</Buy_Tin>
	                        <Buy_Nm>{cust_name}</Buy_Nm>
	                        <Fro_Place>{from_place}</Fro_Place>
	                        <To_Place>{to_place}</To_Place>
	                        <Goods_Desc>Corrugated Boxes</Goods_Desc>
	                        <Qty_unit_det>{qty}</Qty_unit_det>
	                        <NetVal>{net_amount}</NetVal>
	                        <TaxVal>{tax_amt}</TaxVal>
	                        <Tr_Veh_Own> </Tr_Veh_Own>
	                        <Veh_No> </Veh_No>
	                        <Gc_Lr_No> </Gc_Lr_No>
	                        <Trans_Goods_Cat>V-A</Trans_Goods_Cat>
	                        <Doc_type>INV</Doc_type>
	                        <Comm_Code>2.00</Comm_Code>
	                        <State_Cat>O</State_Cat>
	                    </Vat505_Det>
					</VAT505_req>
                    """.format(sender_tin=self.sender_tin, inv_no=inv.name, date=posting_date, \
								cust_tin=self.buyer_tin, cust_name=self.customer, \
								qty = qty, net_amount = self.net_amount, tax_amt=self.tax_amount, \
								from_place=self.from_place, to_place=self.to_place).encode('utf-8').decode('utf-8')
		try:
			dom = parseString(xml_data)
			self.xml_data = dom.toxml()
		except:
			frappe.throw("Failed to parse xml {0}".format(xml_data))
		#self.xml_data = xml_data.strip()

	def populate_invoice_details(self):
		inv = frappe.get_doc("Sales Invoice", self.sales_invoice)
		self.from_place = frappe.db.get_value("Address", inv.company +"-Billing", "city")
		self.sender_tin = frappe.db.get_value("Address", inv.company +"-Billing", "gstin")

		self.to_place = frappe.db.get_value("Address", inv.customer +"-Billing", "city")
		self.buyer_tin = frappe.db.get_value("Address", inv.customer +"-Billing", "gstin")
		self.net_amount = inv.net_total
		self.tax_amount = inv.total_taxes_and_charges
		self.customer = inv.customer

	def validate(self):
		if (self.sales_invoice not in self.name):
			frappe.throw("Sales invoice changed after save. Please rename the document")

	def on_update(self):
		self.create_esugam_xml()

def restore_xml_tags(data):
	return data.replace("&lt;", "<").replace("&gt;", ">")

@frappe.whitelist()
def download_xml(invoice):
	esugama_doc = frappe.get_doc("CM ESugama", invoice)
	frappe.local.response.filename = "esugama.xml"
	xml_data = restore_xml_tags(esugama_doc.xml_data)
	frappe.local.response.filecontent = xml_data
	frappe.local.response.type = "download"
