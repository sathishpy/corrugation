# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import xml.dom.minidom

class CMExportData(Document):
	def autoname(self):
		self.name = "Data-{0}:{1}".format(self.from_date, self.to_date)

	def load_data(self):
		self.transaction_items = []
		entries = get_gl_data(self.from_date, self.to_date)
		for entry in entries:
			voucher_entry = frappe.new_doc("CM Transaction Item")
			voucher_entry.posting_date = entry.posting_date
			voucher_entry.voucher_type = entry.voucher_type
			voucher_entry.voucher_no = entry.voucher_no
			if entry.debit != 0:
				voucher_entry.voucher_amount = entry.debit
				voucher_entry.debit = 1
			else:
				voucher_entry.voucher_amount = entry.credit
				voucher_entry.debit = 0

			if (entry.party != None):
				voucher_entry.party = entry.party
			else:
				voucher_entry.party = entry.account
			self.append("transaction_items", voucher_entry)

	def onload(self):
		self.load_data()

	def generate_xml(self):
		print "Generating export data"
		vouchers = [entry.voucher_no for entry in self.transaction_items]
		vouchers = list(set(vouchers))
		dom = get_tally_head()
		for voucher in vouchers:
			entries = [entry for entry in self.transaction_items if entry.voucher_no == voucher]
			invoice = entries[0]
			print "Entry is {0}-{1}".format(invoice.posting_date, invoice.voucher_no)
			request = dom.getElementsByTagName("REQUESTDATA")[0]
			if (invoice.voucher_type == "Purchase Invoice"):
				child = get_tally_purchase_message(entries)
			elif (invoice.voucher_type == "Sales Invoice"):
				child = get_tally_sales_message(entries)
			else:
				child = get_tally_payment_message(entries)
			request.appendChild(child)

		self.export_data = dom.toxml()
		print self.export_data


	def on_update(self):
		self.load_data()
		self.generate_xml()
		#self.export_data()

	def export_data(self):
		self.generate_xml()

def get_tally_head():
	document = """
				<ENVELOPE>
					<HEADER>
						<TALLYREQUEST>Import Data</TALLYREQUEST>
					</HEADER>
					<BODY>
						<IMPORTDATA>
							<REQUESTDESC>
								<REPORTNAME>Vouchers</REPORTNAME>
								<STATICVARIABLES>
									<SVCURRENTCOMPANY>Shree Krishna Packaging Industries</SVCURRENTCOMPANY>
								</STATICVARIABLES>
							</REQUESTDESC>
							<REQUESTDATA>
							</REQUESTDATA>
						</IMPORTDATA>
					</BODY>
				</ENVELOPE>
			"""
	dom = xml.dom.minidom.parseString(document)
	return dom

def get_tally_purchase_message(entries):
	invoice = entries[0]
	document = """
					<TALLYMESSAGE xmlns:UDF="TallyUDF">
						<VOUCHER VCHTYPE="Purchase" ACTION="Create">
							<DATE>{0}</DATE>
							<NARRATION>{1}</NARRATION>
							<VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>
							  <PARTYLEDGERNAME>{2}</PARTYLEDGERNAME>
							  <FBTPAYMENTTYPE>Default</FBTPAYMENTTYPE>
							  <ISOPTIONAL>No</ISOPTIONAL>
							  <EFFECTIVEDATE>{0}</EFFECTIVEDATE>
							  <ISCANCELLED>No</ISCANCELLED>
							  <HASCASHFLOW>No</HASCASHFLOW>
							  <ISINVOICE>No</ISINVOICE>
						</VOUCHER>
					</TALLYMESSAGE>
				""".format(invoice.posting_date.strftime('%Y%m%d'), invoice.voucher_no, invoice.party)
	dom = xml.dom.minidom.parseString(document)
	voucher = dom.getElementsByTagName("VOUCHER")[0]
	for entry in entries:
		partyledger = "Yes"
		deemedpos = "No"
		amount = entry.voucher_amount
		if (entry.debit == 1):
			partyledger = "No"
			deemedpos = "Yes"
			amount = -amount
		entryxml = """
					  <ALLLEDGERENTRIES.LIST>
						  <LEDGERNAME>{0}</LEDGERNAME>
						  <GSTCLASS/>
						  <ISDEEMEDPOSITIVE>{1}</ISDEEMEDPOSITIVE>
						  <LEDGERFROMITEM>No</LEDGERFROMITEM>
						  <REMOVEZEROENTRIES>No</REMOVEZEROENTRIES>
						  <ISPARTYLEDGER>{2}</ISPARTYLEDGER>
						  <AMOUNT>{3}</AMOUNT>
					  </ALLLEDGERENTRIES.LIST>
					""".format(entry.party, deemedpos, partyledger, amount)
		ledger_entry = xml.dom.minidom.parseString(entryxml).documentElement
		voucher.appendChild(ledger_entry)

	return dom.documentElement

def get_tally_sales_message(entries):
	invoice = entries[0]
	document = """
					<TALLYMESSAGE>
						<VOUCHER VCHTYPE="Sales" ACTION="Create">
							<ADDRESS.LIST>
								<ADDRESS></ADDRESS>
							</ADDRESS.LIST>
							<BASICBUYERADDRESS.LIST>
								<BASICBUYERADDRESS></BASICBUYERADDRESS>
							</BASICBUYERADDRESS.LIST>
							<DATE>{0}</DATE>
							<NARRATION></NARRATION>
							<VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
							<VOUCHERNUMBER>{1}</VOUCHERNUMBER>
						</VOUCHER>
					</TALLYMESSAGE>
				""".format(invoice.posting_date.strftime('%Y%m%d'), invoice.voucher_no)
	dom = xml.dom.minidom.parseString(document)
	return dom.documentElement

def get_tally_payment_message(entries):
	invoice = entries[0]
	document = """
					<TALLYMESSAGE>
						<VOUCHER VCHTYPE="Payment" ACTION="Create">
							<DATE>{0}</DATE>
							<NARRATION></NARRATION>
							<VOUCHERTYPENAME>Payment</VOUCHERTYPENAME>
							<VOUCHERNUMBER>{1}</VOUCHERNUMBER>
							<PARTYLEDGERNAME>{2}</PARTYLEDGERNAME>
							<FBTPAYMENTTYPE>Default</FBTPAYMENTTYPE>
							<EFFECTIVEDATE>{0}</EFFECTIVEDATE>
							<ISPOSTDATED>No</ISPOSTDATED>
							<ISINVOICE>No</ISINVOICE>
						</VOUCHER>
					</TALLYMESSAGE>
				""".format(invoice.posting_date.strftime('%Y%m%d'), invoice.voucher_no, invoice.party)
	dom = xml.dom.minidom.parseString(document)
	voucher = dom.getElementsByTagName("VOUCHER")[0]
	for entry in entries:
		partyledger = "Yes"
		deemedpos = "No"
		amount = entry.voucher_amount
		if (entry.debit == 0):
			partyledger = "No"
			deemedpos = "Yes"
			amount = -amount
		entryxml = """
					<ALLLEDGERENTRIES.LIST>
						<LEDGERNAME>{0}</LEDGERNAME>
						<ISDEEMEDPOSITIVE>{1}</ISDEEMEDPOSITIVE>
						<LEDGERFROMITEM>No</LEDGERFROMITEM>
						<REMOVEZEROENTRIES>No</REMOVEZEROENTRIES>
						<ISPARTYLEDGER>{2}</ISPARTYLEDGER>
						<AMOUNT>{3}</AMOUNT>
					</ALLLEDGERENTRIES.LIST>
					""".format(entry.party, deemedpos, partyledger, amount)
		ledger_entry = xml.dom.minidom.parseString(entryxml).documentElement
		voucher.appendChild(ledger_entry)

	return dom.documentElement

def get_gl_data(from_dt, to_dt):
	query = """
        	select  posting_date, account, sum(debit) as debit, sum(credit) as credit,
                    voucher_type, voucher_no, party, against_voucher
            from `tabGL Entry`
			where voucher_type != 'Stock Entry' and voucher_type != 'Delivery Note'
			 		and voucher_type != 'Purchase Receipt' and posting_date between '{0}' and '{1}'
            group by voucher_type, voucher_no, account
            order by posting_date, voucher_no, account""".format(from_dt, to_dt)
	print ("Executing query: {0}".format(query))

	gl_entries = frappe.db.sql(query, as_dict=1)
	#XXX: Replace with company abrv
	for entry in gl_entries:
		entry.account = entry.account.replace("- SKPI", "")

	return gl_entries
