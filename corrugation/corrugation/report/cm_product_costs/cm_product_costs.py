# Copyright (c) 2013, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import datetime
import calendar
from frappe import _


def execute(filters=None):
<<<<<<< HEAD
	consolidated = filters.get("consolidated")
	start_date = filters.get("from_date")
	end_date = filters.get("to_date")

	columns = get_columns(consolidated)
	entries = get_result(start_date, end_date, consolidated)
	entries = sorted(entries, key=lambda x: x[len(columns) - 1])
	chart = get_chart_data(columns, entries)
	return columns, entries, None, chart

def get_result(start_date, end_date, consolidated):
	print("Generating production costs report({0})for orders between {1} and {2}".format(start_date, end_date, consolidated))
	act_indirect_cost = get_total_expenses(start_date, end_date)
	all_planned_op_cost = 0
	result = []
	prod_entries = frappe.db.sql("""select name, box, box_desc, mfg_date, mfg_qty, planned_rm_cost, act_rm_cost
									from `tabCM Production Order`
									where mfg_date between '{0}' and '{1}'"""\
									.format(start_date, end_date),as_dict=1)

	for order in prod_entries:
		box_desc = frappe.get_doc("CM Box Description", order.box_desc)
		bom_op_cost = box_desc.item_prod_cost + box_desc.item_transport_cost + box_desc.item_other_cost
		all_planned_op_cost += (bom_op_cost * order.mfg_qty)

	for order in prod_entries:
		box_desc = frappe.get_doc("CM Box Description", order.box_desc)
		bom_op_cost = box_desc.item_prod_cost + box_desc.item_transport_cost + box_desc.item_other_cost

		planned_rm_cost = order.planned_rm_cost * order.mfg_qty
		act_rm_cost = order.act_rm_cost * order.mfg_qty
		planned_op_cost = bom_op_cost * order.mfg_qty
		act_op_cost = act_indirect_cost * planned_op_cost/all_planned_op_cost

		op_profit = (planned_op_cost - act_op_cost)
		planned_cost = planned_op_cost + planned_rm_cost
		act_cost = act_op_cost + act_rm_cost

		#prod_order = frappe.get_doc("CM Production Order", order.name)
		#paper_qty = prod_order.get_used_paper_qty()

		sales_price = frappe.db.get_value("Item", order.box, "standard_rate") * order.mfg_qty
		int_loss = 0
		profit = sales_price - act_cost - int_loss
		profit_percent = profit * 100/act_cost

		if (consolidated):
			entry = next((entry for entry in result if entry[0] == order.box), None)
			if (entry is not None):
				print("Updating entry for {0}".format(order.box))
				entry[1] += planned_rm_cost
				entry[2] += act_rm_cost
				entry[3] += op_profit
				entry[4] += planned_cost
				entry[5] += act_cost
				entry[6] += sales_price
				entry[7] += profit
				entry[8] = (entry[7] * 100)/entry[5]
			else:
				result.append([order.box, planned_rm_cost, act_rm_cost, op_profit, planned_cost, act_cost, sales_price, profit, profit_percent])
		else:
			result.append([order.box, order.mfg_date, order.name, planned_rm_cost, act_rm_cost, op_profit, planned_cost, act_cost, sales_price, profit, profit_percent])

	#result.append(["", "", "", "", "", "", "", "","",""])

	return result

def get_columns(consolidated):
	columns = [_("Box Name") + ":Link/Item:150"]
	if (not consolidated):
		columns += [_("Production Date") + ":Date:120", _("Production") + ":Link/CM Production Order:200"]
	columns += [_("Planned Item Cost") + ":Currency:120", _("Actual Item Cost") + ":Currency:120",
			 _("Operating Profit") + ":Currency:120", _("Planned Cost") + ":Currency:100", _("Actual Cost") + ":Currency:100",
			  _("Sales Cost") + ":Currency:100", _("Profit") + ":Currency:100", _("Profit %") + ":Percent:100"]
	return columns

def get_total_expenses(start_date, end_date):
	expenses = frappe.db.sql("""select entry.name as name, it.account as account, it.debit as debit
								from `tabJournal Entry` as entry JOIN `tabJournal Entry Account` as it
								on it.parent=entry.name
								where entry.voucher_type='Journal Entry' and it.debit>0 and entry.docstatus=1
									and entry.posting_date between '{0}' and '{1}'"""\
								.format(start_date, end_date),as_dict=1)
	expense_total = 0

	for expense_entry in expenses:
		parent = frappe.db.get_value("Account", expense_entry.account, "parent_account")
		if ("Indirect Expenses" not in parent): continue
=======
    columns = get_columns()
    entries = get_result(filters)
    for entry in entries:
        print entry

    return columns, entries

def get_result(filters=None):
	print filters

	start_date = filters.get("from_date")
	end_date = filters.get("to_date")
	print("Genarating report from {0} to {1}".format(start_date, end_date))

	act_indirect_cost = get_total_expenses(start_date, end_date)
	per_box_op_cost = get_op_cost_per_box(start_date, end_date)

	total_bom_rm_cost = total_bom_op_cost = total_act_rm_cost = total_act_op_cost = total_bom_cost = total_act_cost = total_production = 0
	result = []
	stock_entries = frappe.db.sql("""select name, posting_date, production_order
									from `tabStock Entry`
									where production_order is not NULL and posting_date between '{0}' and '{1}'"""\
									.format(start_date, end_date),as_dict=1)
	for se in stock_entries:
		print ("--------------------------------------------------------------")
		print "Processing stock entry {0} on {1} for {2}".format(se.name, se.posting_date, se.production_order)

		order = frappe.get_doc("Production Order", se.production_order)
		stock_entry = frappe.get_doc("Stock Entry", se.name)
		bom_entries = frappe.db.sql("""select item_rm_cost, item_prod_cost
										from `tabCM Box Description`
										where item_bom='{0}'""".format(order.bom_no), as_dict=1)
		print bom_entries[0]

		act_rm_cost = 0
		item_qty = 0
		for sitem in stock_entry.items:
			item = frappe.get_doc("Stock Entry Detail", sitem.name)
			if (item.s_warehouse is not None):
				act_rm_cost += item.amount
				print("RM:{0}    Price:{1}".format(item.item_name, item.amount))
			else:
				print("Item:{0}  Qty:{1}".format(item.item_name, item.qty))
				item_qty += item.qty

		if (item_qty == 0): continue

		bom_rm_cost = bom_entries[0].item_rm_cost * item_qty
		bom_op_cost = bom_entries[0].item_prod_cost * item_qty
		act_op_cost = per_box_op_cost * item_qty

		bom_cost = bom_rm_cost + bom_op_cost
		act_cost = act_rm_cost + act_op_cost

		sales_price = stock_entry.total_incoming_value
		int_loss = 0
		print("Sales Price={0} Actual cost={1}".format(sales_price, act_cost))
		profit = ((sales_price - act_cost - int_loss) * 100)/act_cost

		total_bom_rm_cost += bom_rm_cost
		total_bom_op_cost += bom_op_cost
		total_act_rm_cost += act_rm_cost
		total_act_op_cost += act_op_cost
		total_bom_cost += bom_cost
		total_act_cost += act_cost
		total_production += sales_price

		result.append([order.production_item, se.posting_date, se.name, bom_rm_cost, act_rm_cost, bom_op_cost, act_op_cost, bom_cost, act_cost, profit])

	total_profit = ((total_production - total_act_cost) * 100 / total_act_cost)
	result.append(["", "", "", "", "", "", "", "","",""])
	result.append(["Total", "", "", total_bom_rm_cost, total_act_rm_cost, total_bom_op_cost, total_act_op_cost, total_bom_cost, total_act_cost, total_profit])

	return result

def get_columns():
	columns = [
			_("Product Name") + ":Link/Item:150", _("Production Date") + ":Date:120", _("Stock Entry") + ":Link/Stock Entry:100",
			_("BOM Material Cost") + ":Float:100", _("Actual Material Cost") + ":Float:100",
			_("BOM Operation Cost") + ":Float:100", _("Actual Operation Cost") + ":Float:100",
			_("BOM Cost") + ":Float:100", _("Actual Cost") + ":Float:100",
			  _("Profit") + ":Float:100",
			]
	return columns

def get_op_cost_per_box(start_date, end_date):
	op_cost = get_total_expenses(start_date, end_date)
	(boxes, production) = get_production_details(start_date, end_date)
	return op_cost/boxes

def get_total_expenses(start_date, end_date):
	expenses = frappe.db.sql("""select name, total_debit
									from `tabJournal Entry`
									where voucher_type='Journal Entry' and posting_date between '{0}' and '{1}'"""\
									.format(start_date, end_date),as_dict=1)

	expense_total = 0

	for expense_entry in expenses:
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
		expense = frappe.get_doc("Journal Entry", expense_entry.name)
		#print("{0}    {1}".format(expense.title, expense.total_debit))
		expense_total += expense.total_debit

	return expense_total

<<<<<<< HEAD
def get_chart_data(columns, data):
	labels = [d[0] for d in data]

	last_idx = len(columns) - 1
	planned_cost, actual_cost, sales_price, total_profit, profit_percent = [], [], [], [], []
	for d in data:
		planned_cost.append(int(d[last_idx-4]))
		actual_cost.append(int(d[last_idx-3]))
		sales_price.append(int(d[last_idx-2]))
		total_profit.append(int(d[last_idx-1]))
		profit_percent.append(round(d[last_idx], 2))

	datasets = [{'title': 'Planned Cost', 'values': planned_cost},
				{'title': 'Actual Cost', 'values': actual_cost},
				{'title': 'Sales Price', 'values': sales_price},
				{'title': 'Total Profit', 'values': total_profit},
				{'title': 'Profit Percent', 'values': profit_percent}]

	chart = {
		"data": {
                    'labels': labels,
                    'datasets': datasets
                }
	}

	chart["type"] = "line"

	return chart
=======
def get_production_details(start_date, end_date):
	prod_orders = frappe.get_all("Production Order", fields={"status":"Completed"})
	total_boxes = total_production = 0

	for order_entry in prod_orders:
		order = frappe.get_doc("Production Order", order_entry.name)
		stock_entry = frappe.get_doc("Stock Entry", {"production_order":order.name})
		total_boxes += order.produced_qty
		total_production += stock_entry.total_outgoing_value

	return (total_boxes, total_production)
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
