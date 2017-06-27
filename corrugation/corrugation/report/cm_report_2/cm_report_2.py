# Copyright (c) 2013, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import datetime
import calendar


def execute(filters=None):
	print "YYYYYYYYYYYYYYYYYYYYYYYYYY",filters
	columns, data = [], []	
	columns = get_columns ()
	# form header with year and month
	cm_product_cost_entries = frappe.db.sql("""select cm_year, cm_month from `tabCM Product Costs`""",as_dict=1)
	print cm_product_cost_entries
	for en in cm_product_cost_entries:
		l = ()
		lt = list(l)
		lt.append("<b>"+en.cm_month+"</b>")
		lt.append("<b>"+str(en.cm_year)+"</b>")
		data.append (lt)

		month = list(calendar.month_abbr).index(en.cm_month)
		start_date = datetime.date(year=int(en.cm_year), month=month, day=1)
		end_date = datetime.date(year=int(en.cm_year), month=month, day=15)
		stock_entries = frappe.db.sql("""select name, posting_date, production_order
		
										from `tabStock Entry`
										where production_order is not NULL and posting_date between '{0}' and '{1}'"""\
										.format(start_date, end_date),as_dict=1)
		cm_act_indirect_cost = get_total_expenses(month)
		per_box_op_cost = get_op_cost_per_box(month)
		cm_est_direct_cost = cm_act_direct_cost = cm_total_production = cm_est_indirect_cost = 0
		product = ()
		product_t = list(product)
		product_list = []
		for se in stock_entries:
			print ("--------------------------------------------------------------")
			print "Processing stock entry {0} on {1} for {2}".format(se.name, se.posting_date, se.production_order)

			order = frappe.get_doc("Production Order", se.production_order)
			stock_entry = frappe.get_doc("Stock Entry", se.name)
			bom = frappe.get_doc("BOM", order.bom_no)

			per_item_cost = bom.base_total_cost/bom.quantity
			print ("Item BOM Cost {0} Item Op Cost {1}".format(per_item_cost, per_box_op_cost))

			rm_cost = 0
			item_qty = 0
			product = []
			for sitem in stock_entry.items:
				item = frappe.get_doc("Stock Entry Detail", sitem.name)
				if (item.s_warehouse is not None):
					rm_cost += item.amount
					print("RM:{0}    Price:{1}".format(item.item_name, item.amount))
				else:
					print("Item:{0}  Qty:{1}".format(item.item_name, item.qty))
					item_qty += item.qty

			if (item_qty == 0): continue

			#product = frappe.new_doc("CM Product Cost")
			cm_product = order.production_item
			cm_date = se.posting_date
			cm_stock_info = se.name
			cm_bom_cost = per_item_cost * item_qty
			cm_act_cost = rm_cost + (per_box_op_cost * item_qty)
			cm_sales_price = stock_entry.total_incoming_value
			cm_int_loss = 0
			cm_profit = (cm_sales_price - cm_act_cost - cm_int_loss) * 100 / cm_act_cost

			cm_est_direct_cost += product.cm_bom_cost
			cm_act_direct_cost += product.cm_act_cost
			cm_total_production += product.cm_sales_price
			product_t.append (cm_date)
			product_t.append (cm_product)
			product_t.append (cm_bom_cost)
			product_t.append (cm_act_cost)
			product_t.append (cm_profit)
			product_list.append (product_t)
		l = ("Estimated Materail Cost", "Estimated Operation Cost", "Actual Materila Cost", "Actual Operation Cost", "Total Production Cost")
		lt = list(l)
		data.append (lt)
		l = ()
		lt = list (l)
		cm_est_direct_cost = cm_act_direct_cost = cm_total_production = 0
		lt.append (cm_est_direct_cost)
		lt.append (cm_est_indirect_cost)
		lt.append (cm_act_direct_cost)
		lt.append (cm_act_indirect_cost)
		lt.append (cm_total_production)
		data.append (lt)
		data.append (("Date", "Product", "BOM Cost", "ACT Cost", "Profit"));
		for en in product_list:
			data.append (en)
		if (len(product_list) == 0):
			data.append (("-", "-", "-", "-", "-"));
				
	return columns, data


def get_op_cost_per_box(month):
	op_cost = get_total_expenses(month)
	(boxes, production) = get_production_details(month)
	return op_cost/boxes

def get_total_expenses(month):
	#expenses = frappe.get_all("Journal Entry", fields={"voucher_type":"Journal Entry"})
	thisyear = datetime.datetime.now().year
	start_date = datetime.date(year=thisyear, month=month, day=1)
	end_date = datetime.date(year=thisyear, month=month, day=30)

	expenses = frappe.db.sql("""select name, total_debit
									from `tabJournal Entry`
									where voucher_type='Journal Entry' and posting_date between '{0}' and '{1}'"""\
									.format(start_date, end_date),as_dict=1)

	expense_total = 0

	for expense_entry in expenses:
		expense = frappe.get_doc("Journal Entry", expense_entry.name)
		#print("{0}    {1}".format(expense.title, expense.total_debit))
		expense_total += expense.total_debit

	return expense_total

def get_production_details(month):
	prod_orders = frappe.get_all("Production Order", fields={"status":"Completed"})
	total_boxes = total_production = 0

	for order_entry in prod_orders:
		order = frappe.get_doc("Production Order", order_entry.name)
		stock_entry = frappe.get_doc("Stock Entry", {"production_order":order.name})
		total_boxes += order.produced_qty
		total_production += stock_entry.total_outgoing_value

	return (total_boxes, total_production)

def get_columns():
        return [
                {
                        "fieldname": "1",
                        "width": 145
                },
                {
                        "fieldname": "2",
                        "width": 150
                },
                {
                        "fieldname": "3",
                        "width": 120
                },
                {
                        "fieldname": "4",
                        "width": 130
                },
                {
                        "fieldname": "5",
                        "width": 130
                }
	       ]
