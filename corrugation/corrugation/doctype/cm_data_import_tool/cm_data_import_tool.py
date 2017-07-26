# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import xml.dom.minidom
import csv, os, re
from datetime import datetime
from frappe import _
from erpnext.controllers.item_variant import create_variant, find_variant
from frappe.utils import nowdate

class CMDataImportTool(Document):
	def autoname(self):
		self.name = self.data_type + "-import-data"

	def extract_data(self):
		if self.filename is None: return
		self.party_items = self.account_items = self.box_items = self.roll_items = self.voucher_items = []
		print "Retrieving data from file {0}".format(self.filename)
		filename = self.filename.split("/")[-1]

		filepath = frappe.get_site_path("private", "files", filename);
		if (not os.path.isfile(filepath)):
			filepath = frappe.get_site_path("public", "files", filename);
		if (not os.path.isfile(filepath)):
			frappe.throw("Unable to find the uploaded  file {0}".format(self.filename))
		if (self.data_type == "Party"):
			self.extract_party_details(filepath)
		elif self.data_type == "Roll":
			self.extract_roll_details(filepath)
		elif self.data_type == "Box":
			self.extract_box_details(filepath)
		elif self.data_type == "Account":
			self.extract_account_details(filepath)
		elif self.data_type == "DayBook":
			self.extract_daybook_details(filepath)

	def import_data(self):
		if self.filename is None: return
		if (self.data_type == "Party"):
			self.import_parties()
		elif self.data_type == "Roll":
			self.import_rolls()
		elif self.data_type == "Box":
			self.import_boxes()
		elif self.data_type == "Account":
			self.import_accounts()
		elif self.data_type == "DayBook":
			self.import_daybook()

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
			party_entry.opening_balance = get_opening_balance(ledger)
			self.append("party_items", party_entry)

	def import_parties(self):
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
			else:
				party_entry = frappe.new_doc("Supplier")
				party_entry.supplier_name = party.party_name
				party_entry.supplier_type = "Local"
			party_entry.tax_id = party.party_tin
			party_entry.insert()
			self.add_party_address(party)

			if (party.opening_balance != 0):
				invoice = get_temp_sales_and_purchase_invoice(party.party_name, party.party_type, party.opening_balance)
				invoice.save()
				invoice.submit()

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

	def extract_account_details(self, filepath):
		self.account_items = []
		self.total_debit = self.total_credit = 0
		grouped_accounts = {}

		print("File is {0}".format(filepath))
		dom = xml.dom.minidom.parse(filepath)
		ledger_entries = dom.getElementsByTagName("LEDGER")
		for ledger in ledger_entries:
			parent = ledger.getElementsByTagName("PARENT")[0]
			parent_type = getText(parent).strip()

			if "Sundry" in parent_type: continue
			if (not parent_type):
				print ("Ignoring account {0} whaving no paprent type".format(ledger.getAttribute("NAME")))
				continue

			opening_balance = get_opening_balance(ledger)

			account_entry = frappe.new_doc("CM Import Account Item")
			account_entry.account_name = ledger.getAttribute("NAME")

			account_type = get_erpnext_mapped_account_group(parent_type)
			mapped_parents = frappe.db.sql("""select name from `tabAccount` where name LIKE '%{0}%'""".format(account_type), as_dict=1)
			if (len(mapped_parents) > 0):
				account_entry.account_type = mapped_parents[0].name

			if (parent_type in grouped_accounts):
				grouped_accounts[parent_type].append(account_entry)
			else:
				grouped_accounts[parent_type] = [account_entry]

			if (opening_balance < 0):
				self.total_debit += (opening_balance * -1)
			else:
				self.total_credit += opening_balance
			account_entry.opening_balance += opening_balance

			print("Creating account entry for {0}:{1}".format(parent_type, account_entry.account_name))
			account_entry.mapped_account = get_erpnext_mapped_account(account_entry.account_name, account_entry.account_type)

		for (k,v) in grouped_accounts.items():
			[self.append("account_items", item) for item in v]

	def map_new_accounts(self):
		for account_item in self.account_items:
			if (is_sales_or_purchase(account_item.account_type)): continue
			if (account_item.mapped_account is None):
				new_account = frappe.new_doc("Account")
				new_account.account_name = trim_account(account_item.account_name)
				new_account.parent_account = account_item.account_type
				if ("Bank" in new_account.parent_account):
					new_account.account_type = "Bank"
				new_account.is_group = 0
				print("Creating new account {0}".format(new_account.account_name))
				new_account.save()
				account_item.mapped_account = new_account.name

			map_item = frappe.db.get_value("""select account from `tabCM Account Mapper` where name = '{0}'""".format(account_item.mapped_account))
			if (map_item is not None): continue

			map_item = frappe.new_doc("CM Account Mapper")
			map_item.account = trim_account(account_item.account_name)
			map_item.mapped_account = account_item.mapped_account
			map_item.save()

	def extract_daybook_details(self, filepath):
		self.voucher_items, self.total_debit, self.total_credit = [], 0, 0
		print("File is {0}".format(filepath))

		dom = xml.dom.minidom.parse(filepath)
		voucher_entries = dom.getElementsByTagName("VOUCHER")
		end_idx = min(self.start_idx + 100, len(voucher_entries))
		for idx in range(self.start_idx, end_idx):
			voucher = voucher_entries[idx]
			voucher_type = getText(voucher.getElementsByTagName("VOUCHERTYPENAME")[0])
			date = datetime.strptime(getText(voucher.getElementsByTagName("DATE")[0]), '%Y%m%d').date()
			entries = voucher.getElementsByTagName("ALLLEDGERENTRIES.LIST")
			for entry in entries:
				party = trim_account(getText(entry.getElementsByTagName("LEDGERNAME")[0]))
				item = frappe.new_doc("CM Voucher Item")
				item.voucher_date = date
				if (voucher_type == "Payment"):
					invoice_count = entry.getElementsByTagName("BILLALLOCATIONS.LIST").length
					if (invoice_count == 0): voucher_type = "Journal"
				item.voucher_type = voucher_type
				item.party = party
				item.voucher_amount = float(getText(entry.getElementsByTagName("AMOUNT")[0]))
				item.voucher_remark = getText(voucher.getElementsByTagName("NARRATION")[0])
				print ("Handling {0} for {1}: {2}".format(voucher_type, party, item.voucher_amount))
				self.append("voucher_items", item)
				(voucher_type, date) = None, None
		self.start_idx = end_idx
		print("Daybook extraction completed for {0} items".format(end_idx))

	def import_daybook(self):
		temp_item = create_temp_item("Temp-Item", "Products")

		for idx in range(0, len(self.voucher_items)):
			voucher = self.voucher_items[idx]
			idx += 1
			date, party, amount, remark = voucher.voucher_date, voucher.party, voucher.voucher_amount, voucher.voucher_remark
			invoice = None
			if (voucher.voucher_type == "Purchase"):
				purchase_item = self.voucher_items[idx]
				idx = idx + 1
				purchase_amount = purchase_item.voucher_amount * -1
				invoice = get_temp_sales_and_purchase_invoice(voucher.party, "Creditors", purchase_amount)
				invoice.posting_date = voucher.voucher_date
				tax_amount = 0
				while idx < len(self.voucher_items) and self.voucher_items[idx].voucher_type is None:
					tax_item = self.voucher_items[idx]
					idx = idx + 1
					tax_amount += (tax_item.voucher_amount * -1)
					invoice = add_tax_to_invoice(invoice, (tax_item.voucher_amount * -1), tax_item.party)
				expected_amount = float(purchase_amount + tax_amount)
				if (expected_amount != voucher.voucher_amount):
					print("Purchase amount {0}({1}+{2}) doesn't match the total amount {3} for {4}".format(expected_amount, purchase_amount, tax_amount, voucher.voucher_amount, voucher.party))
			elif (voucher.voucher_type == "Sales"):
				sales_item = self.voucher_items[idx]
				idx = idx + 1
				sale_amount = sales_item.voucher_amount
				invoice = get_temp_sales_and_purchase_invoice(voucher.party, "Debtors", sale_amount)
				invoice.posting_date = voucher.voucher_date
				tax_amount = 0
				while idx < len(self.voucher_items) and self.voucher_items[idx].voucher_type is None:
					tax_item = self.voucher_items[idx]
					idx = idx + 1
					tax_amount += tax_item.voucher_amount
					invoice = add_tax_to_invoice(invoice, tax_item.voucher_amount, tax_item.party)
				if ((sale_amount + tax_amount) != (voucher.voucher_amount * -1)):
					frappe.throw("Sale amount {0} and tax {1} doesn't match the total amount for {2}".format(sale_amount, tax_amount, voucher.party))
			elif (voucher.voucher_type == "Receipt"):
				to_item = self.voucher_items[idx]
				idx += 1
				invoice = create_payment_entry(date, idx, "Receive", party, to_item.party, amount)
			elif (voucher.voucher_type == "Payment"):
				from_item = self.voucher_items[idx]
				idx = idx + 1
				if from_item.voucher_amount < 0:
					je, je_amount = create_new_journal_entry(date, remark, "Journal Entry"), 0
					while from_item.voucher_amount < 0:
						je_amount += from_item.voucher_amount
						update_journal_entry_balance(je, get_erpnext_mapped_account(from_item.party), from_item.voucher_amount * -1)
						from_item = self.voucher_items[idx]
						idx = idx + 1
					update_journal_entry_balance(je, get_erpnext_mapped_account(from_item.party), je_amount)
					je.save()
				invoice = create_payment_entry(date, idx, "Pay", party, from_item.party, amount)
			elif (voucher.voucher_type in ["Journal", "Contra"]):
				invoice = create_new_journal_entry(date, remark, voucher.voucher_type + " Entry")
				account = get_erpnext_mapped_account(party)
				while idx < len(self.voucher_items) and self.voucher_items[idx].voucher_type is None:
					update_journal_entry_balance(invoice, account, amount * -1)
					voucher = self.voucher_items[idx]
					idx = idx + 1
					account, amount = get_erpnext_mapped_account(voucher.party), voucher.voucher_amount
				update_journal_entry_balance(invoice, account, amount * -1)

			else: continue
			print("Saving the invoice for {0} for amount {1}".format(voucher.party, voucher.voucher_amount))
			invoice.save()

	def extract_roll_details(self, filepath):
		self.party_items = []
		self.roll_items = []

		validate_headers(filepath, ["Colour", "BF", "GSM", "Deck", "Rate", "Weight"])
		with open(filepath) as csvfile:
			rolls = csv.DictReader(csvfile)
			for roll in rolls:
				roll_item = frappe.new_doc("CM Import Roll Item")
				roll_item.paper_color = roll["Colour"]
				roll_item.paper_bf = roll["BF"]
				roll_item.paper_gsm = roll["GSM"]
				roll_item.paper_deck = roll["Deck"]
				roll_item.paper_rate = roll["Rate"]
				roll_item.roll_weight = roll["Weight"]
				self.append("roll_items", roll_item)

	def import_rolls(self):
		last_idx = frappe.db.count("CM Paper Roll")
		idx = last_idx + 1
		for roll in self.roll_items:
			variant_args = {"Colour": roll.paper_color, "BF": roll.paper_bf, "GSM": roll.paper_gsm, "Deck": roll.paper_deck}
			paper = find_variant("Paper-RM", variant_args)
			if (paper == None):
				print ("Creating Paper for args {0} weight: {1}".format(variant_args, roll.roll_weight))
				paper_doc = create_variant("Paper-RM", variant_args)
				if (paper_doc != None):
					paper_doc.valuation_rate = roll.paper_rate
					paper_doc.save(ignore_permissions=True)
					paper = paper_doc.name
				else:
					frappe.throw("Failed to create the paper variant")
					continue

			paper_item = frappe.get_doc("Item", paper)
			paper_item.opening_stock = roll.roll_weight
			print("Updating paper {0} stock to {1}".format(paper, paper_item.opening_stock))
			paper_item.set_opening_stock()
			paper_item.save(ignore_permissions=True)

			paper_roll = frappe.new_doc("CM Paper Roll")
			paper_roll.paper = paper
			paper_roll.number = idx
			idx = idx + 1
			paper_roll.weight = roll.roll_weight
			paper_roll.status = "Ready"
			paper_roll.insert()

	def extract_box_details(self, filepath):
		self.party_items, self.roll_items, self.box_items = [], [], []
		validate_headers(filepath, ["Name", "Code", "Length", "Width", "Height", "Ply", "Top", "Rate"])
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
				box_item.top_type = box["Top"]
				box_item.rate = box["Rate"]
				self.append("box_items", box_item)

	def import_boxes(self):
		for box_item in self.box_items:
			box = frappe.new_doc("CM Box")
			box.box_name = box_item.box_name
			box.box_code = box_item.box_code
			box.box_length = box_item.length
			box.box_width = box_item.width
			box.box_height = box_item.height
			box.box_top_type = box_item.top_type
			box.box_ply_count = box_item.ply
			box.box_rate = box_item.rate
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
	#print "Text is {0}".format(''.join(text))
	return ''.join(text).strip()


def get_opening_balance(ledger):
	balance = 0
	balance_list = ledger.getElementsByTagName("OPENINGBALANCE")
	if (len(balance_list) > 0):
		balance = balance_list[0]
		#print ("Balance is {0}".format(getText(balance)))
		balance = float(getText(balance))
	return balance

def validate_headers(filepath, required_field_names):
	with open(filepath) as csvfile:
		read_csv_file = csv.DictReader(csvfile)
		field_names, missing_fields = [], []
		read_csv_file = csv.reader(csvfile, delimiter= str(","))
		field_names = (next(read_csv_file))
		print "hearder is {0}".format(field_names)
		for required_field in required_field_names:
			if required_field not in field_names:
				missing_fields.append(required_field)
	if len(missing_fields) > 0:
		frappe.throw("fields {0} missing".format(missing_fields))

def get_erpnext_mapped_account_group(acct_group):
	tally_to_erp_map = {
		"Securities and Deposits": ["Deposits (Asset)"],
		"Cash In Hand": ["Cash-in-hand"],
		"Bank Accounts": ["Bank Accounts"],
		"Duties and Taxes": ["Duties & Taxes"],
		"Unsecured Loans": ["Unsecured Loans"],
		"Fixed Assets": ["Fixed Assets"],
		"Loans (Liabilities)": ["Loans (Liability)"],
		"Accounts Payable": ["Sundry Creditors"],
		"Accounts Receivable": ["Sundry Debtors"],
		"Bank Overdraft Account": ["Bank OD A/c"],
		"Direct Expenses": ["Purchase Accounts"],
		"Indirect Expenses": ["Indirect Expenses", "Misc. Expenses (ASSET)"],
	}
	for (k, v) in tally_to_erp_map.items():
		if (acct_group in v): return k

def get_erpnext_mapped_account(account_name, account_type = None):
	trimmed_account = trim_account(account_name)
	mapped_account = frappe.db.get_value("CM Account Mapper", {"account": trimmed_account}, "mapped_account")
	if (mapped_account is None):
		acct = trimmed_account.split()[0]
		parent_cond = ""
		if (account_type is not None):
			parent_cond = "and parent_account='{0}'".format(account_type)
		mapped_accounts = frappe.db.sql("""select name from `tabAccount`
											where name LIKE '%{0}%' {1}""".format(acct, parent_cond), as_dict=1)
		if (len(mapped_accounts) > 0):
			mapped_account = mapped_accounts[0].name
	return mapped_account

def update_journal_entry_balance(je, account, balance):
	if (balance < 0):
		je.append("accounts", {"account": account,
								"debit_in_account_currency": balance * -1})
	else:
		je.append("accounts", {"account": account,
								"credit_in_account_currency": balance})

@frappe.whitelist()
def update_opening_balance(source):
	import_doc = frappe.get_doc("CM Data Import Tool", source)
	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Opening Entry"
	je.remark = "Updating Opening Balance"
	je.posting_date = nowdate()
	je.is_opening = "Yes"
	from erpnext.setup.doctype.company.company import get_name_with_abbr
	temp_account = get_name_with_abbr("Temporary Opening", frappe.defaults.get_defaults().company)
	temp_balance = 0

	for account_item in import_doc.account_items:
		if (is_sales_or_purchase(account_item.account_type)): continue
		if (account_item.mapped_account is not None):
			temp_balance += account_item.opening_balance
			update_journal_entry_balance(je, account_item.mapped_account, account_item.opening_balance)
			print("Setting temp balance to {0} from {1}".format(temp_balance, account_item.opening_balance))
	update_journal_entry_balance(je, temp_account, temp_balance * -1)
	return je.as_dict()

def create_temp_item(item, group):
	if (frappe.db.get_value("Item", item) is not None): return frappe.get_doc("Item", item)
	temp_item = frappe.new_doc("Item")
	temp_item.item_name = temp_item.item_code = item
	temp_item.item_group = group
	temp_item_name = frappe.db.get_value("Item", temp_item.item_code)
	temp_item.insert()
	return temp_item

def get_temp_sales_and_purchase_invoice(party, party_type, balance):
	temp_item = create_temp_item("Temp-Item", "Products")
	invoice = None
	if ("Creditors" in party_type):
		invoice = frappe.new_doc("Purchase Invoice")
		invoice.supplier = party
	else:
		invoice = frappe.new_doc("Sales Invoice")
		invoice.customer = party
		balance = balance * -1
		if (balance < 0): balance *= -1
	invoice.append("items", {
				"item_code": temp_item.item_code,
				"qty": 1,
				"rate": balance
			})
	invoice.set_missing_values()
	return invoice

def add_tax_to_invoice(invoice, tax_amount, tax_account):
	invoice.append("taxes", {
					"charge_type": "Actual",
					"description": "Tax Item",
					"account_head": get_erpnext_mapped_account(tax_account),
					"tax_amount": tax_amount
				})
	invoice.set_missing_values()
	return invoice


def create_payment_entry(date, number, pay_type, party, account, amount):
	pentry = frappe.new_doc("Payment Entry")
	pentry.payment_type = pay_type
	pentry.party = party
	if (pay_type == "Pay"):
		pentry.party_type = "Supplier"
		pentry.paid_from = get_erpnext_mapped_account(account)
	elif (pay_type == "Receive"):
		pentry.party_type = "Customer"
		pentry.paid_to = get_erpnext_mapped_account(account)
	else:
		frappe.throw("Payment type {0} is not supported for data import".format(pay_type))
	pentry.account_type = "Bank"
	if ("Cash" in account):
		pentry.account_type = "Cash"
	pentry.received_amount = pentry.paid_amount = amount
	pentry.reference_no = number
	pentry.reference_date = date
	pentry.setup_party_account_field()
	return pentry

def create_new_journal_entry(date, remark, entry_type):
	jentry = frappe.new_doc("Journal Entry")
	jentry.voucher_type = entry_type
	jentry.remark = remark
	jentry.posting_date = date
	jentry.is_opening = "No"
	return jentry

def is_sales_or_purchase(account):
	matching = [s for s in ["Accounts Payable", "Accounts Receivable"] if s in str(account)]
	return (len(matching) > 0)

def trim_account(account):
	account = re.sub("A\/C$", "", account)
	account = re.sub("A\/c$", "", account)
	account = re.sub("a\/c$", "", account)
	return account

@frappe.whitelist()
def filter_account(doctype, txt, searchfield, start, page_len, filters):
	account_name = filters["account_name"]
	account_type = filters["account_type"]

	filter_query =	"""select name from `tabAccount` where parent_account LIKE '{0}%' and name LIKE '%{1}%'""".format(account_type, txt)
	print "Selecting accounts using query {0}".format(filter_query)
	return frappe.db.sql(filter_query)
