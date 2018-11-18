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
		print ("Retrieving data from file {0}".format(self.filename))
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
		grouped_parties = {}
		self.total_debit, self.total_credit = 0, 0

		ledger_entries = dom.getElementsByTagName("LEDGER")
		for ledger in ledger_entries:
			parent = ledger.getElementsByTagName("PARENT")[0]
			parent_type = getText(parent)
			if "Sundry" not in parent_type: continue
			party_entry = frappe.new_doc("CM Import Party Item")
			party_entry.party_name = ledger.getAttribute("NAME")
			party_entry.party_type = parent_type

			party_entry.opening_balance = get_opening_balance(ledger)
			if (party_entry.opening_balance == 0 and self.ignore_zero_balance): continue
			if ("Creditors" in parent_type):
				self.total_credit += party_entry.opening_balance
			else:
				self.total_debit += party_entry.opening_balance

			addr_node = ledger.getElementsByTagName("ADDRESS.LIST")
			if (len(addr_node) > 0):
				party_entry.party_address = getText(addr_node[0])

			if (parent_type in grouped_parties):
				grouped_parties[parent_type].append(party_entry)
			else:
				grouped_parties[parent_type] = [party_entry]

		for (k,v) in grouped_parties.items():
			[self.append("party_items", item) for item in v]

	def import_parties(self):
		entries = 0
		temp_opening_difference = 0
		for party in self.party_items:
			if party.party_type != "Sundry Debtors" and party.party_type != "Sundry Creditors": continue
			party_entry = None
			print ("Inserting party {0}-{1}".format(party.party_type, party.party_name))
			if (party.party_type == "Sundry Debtors"):
				customer_id = frappe.db.get_value("Customer", filters={"customer_name": party.party_name})
				if (customer_id):
					party_entry = frappe.get_doc("Customer", customer_id)
				else:
					party_entry = frappe.new_doc("Customer")
					party_entry.customer_name = party.party_name
					party_entry.customer_type = "Company"
					party_entry.customer_group = "Commercial"
					party_entry.territory = "India"
					party_entry.insert()
			else:
				supplier_id = frappe.db.get_value("Supplier", filters={"supplier_name": party.party_name})
				if (supplier_id):
					party_entry = frappe.get_doc("Supplier", supplier_id)
				else:
					party_entry = frappe.new_doc("Supplier")
					party_entry.supplier_name = party.party_name
					party_entry.supplier_type = "Local"
					party_entry.insert()
			party_entry.tax_id = party.party_tin
			party_entry.save()
			self.add_party_address(party)

			if (party.opening_balance != 0):
				invoice = get_temp_sales_and_purchase_invoice(party.party_name, party.party_type, party.opening_balance, self.posting_date)
				invoice.save()
				invoice.submit()
				temp_opening_difference += party.opening_balance

	def add_party_address(self, party):
		if (party.party_address is None): return
		addr_list = party.party_address.splitlines(True)
		addr_size = len(addr_list)
		if (addr_size < 1): return

		address = frappe.new_doc("Address")
		new_address = True
		addr_name = frappe.db.get_value("Address", filters={"address_title": party.party_name, "address_type": "Billing"})
		if (addr_name is not None):
			print("Party {0} already has a billing address".format(addr_name))
			address = frappe.get_doc("Address", addr_name)
			new_address = False
		else:
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

		if (not new_address):
			address.save()
			return

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

			if "Sundry" in parent_type and self.ignore_party: continue
			if (not parent_type):
				print ("Ignoring account {0} whaving no paprent type".format(ledger.getAttribute("NAME")))
				continue

			opening_balance = get_opening_balance(ledger)
			if opening_balance == 0 and self.ignore_zero_balance: continue

			account_entry = frappe.new_doc("CM Import Account Item")
			account_entry.account_name = ledger.getAttribute("NAME")

			account_type = get_erpnext_mapped_account_group(parent_type)
			print("Mapping account entry for {0}:{1} in {2}".format(parent_type, account_entry.account_name, account_type))
			mapped_parents = frappe.db.sql("""select name from `tabAccount` where name LIKE '{0}%'""".format(account_type), as_dict=1)
			if (account_type and len(mapped_parents) > 0):
				account_entry.account_type = mapped_parents[0].name
				account = frappe.get_doc("Account", account_entry.account_type)
				if (not account.is_group):
					account.is_group = True
					account.save()
			else:
				print("Failed to find a mapping group for {0}".format(parent_type))

			if (parent_type in grouped_accounts):
				grouped_accounts[parent_type].append(account_entry)
			else:
				grouped_accounts[parent_type] = [account_entry]

			if (opening_balance < 0):
				self.total_debit += (opening_balance * -1)
			else:
				self.total_credit += opening_balance
			account_entry.opening_balance += opening_balance

			account_entry.mapped_account = get_erpnext_mapped_account(account_entry.account_name, account_entry.account_type)

		for (k,v) in grouped_accounts.items():
			[self.append("account_items", item) for item in v]

	def map_new_accounts(self):
		for account_item in self.account_items:
			if (is_sales_or_purchase(account_item.account_type)): continue
			import_account = trim_account(account_item.account_name)
			if (not account_item.mapped_account):
				new_account = frappe.new_doc("Account")
				new_account.account_name = import_account
				new_account.parent_account = account_item.account_type
				if ("Bank" in new_account.parent_account):
					new_account.account_type = "Bank"
				new_account.is_group = 0
				print("Creating new account {0}".format(new_account.account_name))
				new_account.save()
				account_item.mapped_account = new_account.name

			if (frappe.db.get_value("CM Account Mapper", import_account) is not None): continue

			print("Mapping account {0} to {1}".format(import_account, account_item.mapped_account))
			map_item = frappe.new_doc("CM Account Mapper")
			map_item.account = import_account
			map_item.mapped_account = account_item.mapped_account
			map_item.save()

	def extract_daybook_details(self, filepath):
		self.voucher_items, self.total_debit, self.total_credit = [], 0, 0
		print("File is {0}".format(filepath))

		dom = xml.dom.minidom.parse(filepath)
		voucher_entries = dom.getElementsByTagName("VOUCHER")
		end_idx = min(self.start_idx + 50, len(voucher_entries))
		for idx in range(self.start_idx, end_idx):
			voucher = voucher_entries[idx]
			voucher_type = getText(voucher.getElementsByTagName("VOUCHERTYPENAME")[0])
			date = datetime.strptime(getText(voucher.getElementsByTagName("DATE")[0]), '%Y%m%d').date()
			entries = voucher.getElementsByTagName("ALLLEDGERENTRIES.LIST")
			payment_receipt = True
			for entry in entries:
				party = trim_account(getText(entry.getElementsByTagName("LEDGERNAME")[0]))
				item = frappe.new_doc("CM Voucher Item")
				item.voucher_date = date
				if (voucher_type == "Payment"):
					invoice_count = entry.getElementsByTagName("BILLALLOCATIONS.LIST").length
					if (invoice_count == 0): voucher_type = "Journal"
				item.voucher_type = voucher_type
				item.source_party = item.party = party
				if (voucher_type == "Sales"):
					item.party_type = "Customer"
				elif (voucher_type == "Purchase"):
					item.party_type = "Supplier"
				elif ((voucher_type == "Payment" or voucher_type == "Receipt") and payment_receipt):
					payment_receipt = False
					item.party_type = "Supplier" if voucher_type == "Payment" else "Customer"
				else:
					item.party_type = "Account"
					item.party = get_erpnext_mapped_account(party)

				item.voucher_amount = float(getText(entry.getElementsByTagName("AMOUNT")[0]))
				if (voucher.getElementsByTagName("NARRATION").length > 0):
					item.voucher_remark = getText(voucher.getElementsByTagName("NARRATION")[0])
				print ("Handling {0} for {1}: {2}".format(voucher_type, party, item.voucher_amount))
				self.append("voucher_items", item)
				(voucher_type, date) = None, None
		self.start_idx = end_idx
		print("Daybook extraction completed for {0} items".format(end_idx))

	def import_daybook(self):
		temp_item = create_temp_item("Temp-Item", "Products")
		idx = 0
		while idx < len(self.voucher_items):
			voucher = self.voucher_items[idx]
			idx += 1
			date, party, amount, remark = voucher.voucher_date, voucher.party, voucher.voucher_amount, voucher.voucher_remark
			invoice = None
			print("{0}: Importing the {1} invoice for {2} of amount {3}".format(idx, voucher.voucher_type, voucher.party, voucher.voucher_amount))
			if (voucher.voucher_type == "Purchase"):
				purchase_item = self.voucher_items[idx]
				idx = idx + 1
				purchase_amount = purchase_item.voucher_amount * -1
				invoice = get_temp_sales_and_purchase_invoice(voucher.party, "Creditors", purchase_amount, voucher.voucher_date)
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
				invoice = get_temp_sales_and_purchase_invoice(voucher.party, "Debtors", sale_amount, voucher.voucher_date)
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
						update_journal_entry_balance(je, from_item.party, from_item.voucher_amount * -1)
						from_item = self.voucher_items[idx]
						idx = idx + 1
					update_journal_entry_balance(je, from_item.party, je_amount)
					je.save()
					je.submit()
				invoice = create_payment_entry(date, idx, "Pay", party, from_item.party, amount * -1)
			elif (voucher.voucher_type in ["Journal", "Contra"]):
				invoice = create_new_journal_entry(date, remark, voucher.voucher_type + " Entry")
				account = party
				while idx < len(self.voucher_items) and self.voucher_items[idx].voucher_type is None:
					update_journal_entry_balance(invoice, account, amount)
					voucher = self.voucher_items[idx]
					idx = idx + 1
					account, amount = voucher.party, voucher.voucher_amount
				update_journal_entry_balance(invoice, account, amount)
			else:
				print("Unsupported voucher type {0} found".format(voucher.voucher_type))
				continue
			#print ("Trying to save/submit invoice {0}".format(invoice.as_dict()))
			invoice.save()
			invoice.submit()

	def extract_roll_details(self, filepath):
		self.party_items = []
		self.roll_items = []

		validate_headers(filepath, ["Roll No", "Colour", "BF", "GSM", "Deck", "Rate", "Weight"])
		with open(filepath) as csvfile:
			rolls = csv.DictReader(csvfile)
			for roll in rolls:
				roll_item = frappe.new_doc("CM Import Roll Item")
				roll_item.roll_no = roll["Roll No"]
				roll_name = frappe.db.get_value("CM Paper Roll", filters={"number": roll_item.roll_no})
				if (roll_name is not None):
					print("Ignoring the paper roll {0} which is already added".format(roll_name))
					continue
				roll_item.paper_color = roll["Colour"]
				roll_item.paper_bf_gsm = roll["BF"] + "-" + roll["GSM"]
				roll_item.paper_deck = roll["Deck"]
				roll_item.roll_weight = roll["Weight"]
				roll_item.paper_std_rate = roll["Rate"]
				roll_item.paper_val_rate = roll["Landing"]
				self.append("roll_items", roll_item)

	def import_rolls(self):
		for roll in self.roll_items:
			bf_gsm_vals = roll.paper_bf_gsm.split("-")
			if (len(bf_gsm_vals) != 2):
				frappe.throw("BF-GSM value {0} is not in the prescribed format".format(roll.paper_bf_gsm))
			variant_args = {"Colour": roll.paper_color, "BF": int(bf_gsm_vals[0]), "GSM": int(bf_gsm_vals[1]), "Deck": roll.paper_deck}
			paper = find_variant("PPR", variant_args)
			if (paper == None):
				print ("Creating Paper for args {0} weight: {1}".format(variant_args, roll.roll_weight))
				paper_doc = create_variant("PPR", variant_args)
				if (paper_doc != None):
					paper_doc.valuation_rate = roll.paper_val_rate
					paper_doc.standard_rate = roll.paper_std_rate
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
			paper_roll.number = roll.roll_no
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
	billings = ledger.getElementsByTagName("BILLALLOCATIONS.LIST")
	if (len(billings) > 0 and len(billings) == len(balance_list)): return 0
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
		print ("hearder is {0}".format(field_names))
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
		"Fixed Assets": ["Fixed Assets", "Capital Account"],
		"Current Assets": ["Current Assets"],
		"Loans (Liabilities)": ["Loans (Liability)"],
		"Current Liabilities": ["Current Liabilities"],
		"Accounts Payable": ["Sundry Creditors"],
		"Accounts Receivable": ["Sundry Debtors"],
		"Bank Overdraft Account": ["Bank OD A/c"],
		"Direct Expenses": ["Purchase Accounts", "Direct Expenses"],
		"Direct Income": ["Sales Accounts"],
		"Indirect Expenses": ["Indirect Expenses", "Misc. Expenses (ASSET)"],
		"Indirect Income": ["Indirect Incomes"],
		"Loans and Advances (Assets)": ["Loans & Advances (Asset)"]
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
	je.posting_date = import_doc.posting_date
	je.is_opening = "Yes"
	from erpnext.setup.doctype.company.company import get_name_with_abbr
	temp_account = get_name_with_abbr("Temporary Opening", frappe.defaults.get_defaults().company)
	temp_balance = 0

	for account_item in import_doc.account_items:
		if (is_sales_or_purchase(account_item.account_type)): continue
		if (account_item.mapped_account is not None and account_item.opening_balance != 0):
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

def get_temp_sales_and_purchase_invoice(party, party_type, balance, inv_date):
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
	invoice.set_posting_time = True
	invoice.posting_date = inv_date
	invoice.set_missing_values()
	return invoice

def add_tax_to_invoice(invoice, tax_amount, tax_account):
	mapped_account = get_erpnext_mapped_account(tax_account)
	print("Adding tax amount of {0} to {1}".format(tax_amount, mapped_account))
	invoice.append("taxes", {
					"charge_type": "Actual",
					"description": "Tax Item",
					"account_head": mapped_account,
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
		pentry.paid_from = account
	elif (pay_type == "Receive"):
		pentry.party_type = "Customer"
		pentry.paid_to = account
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
	print ("Selecting accounts using query {0}".format(filter_query))
	return frappe.db.sql(filter_query)
