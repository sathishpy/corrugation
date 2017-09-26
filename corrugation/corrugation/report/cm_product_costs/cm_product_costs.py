# Copyright (c) 2013, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import datetime
import calendar
from frappe import _


def execute(filters=None):
	consolidated = filters.get("consolidated")
	start_date = filters.get("from_date")
	end_date = filters.get("to_date")

	columns = get_columns(consolidated)
	entries = get_result(start_date, end_date, consolidated)
	chart = get_chart_data(columns, entries, consolidated)
	return columns, entries, None, chart

def get_result(start_date, end_date, consolidated):
	print("Generating production costs report({0})for orders between {1} and {2}".format(start_date, end_date, consolidated))
	act_indirect_cost = get_total_expenses(start_date, end_date)
	all_bom_op_cost = 0
	result = []
	prod_entries = frappe.db.sql("""select name, box, box_desc, mfg_date, mfg_qty, planned_rm_cost, act_rm_cost
									from `tabCM Production Order`
									where mfg_date between '{0}' and '{1}'"""\
									.format(start_date, end_date),as_dict=1)

	for order in prod_entries:
		box_desc = frappe.get_doc("CM Box Description", order.box_desc)
		bom_op_cost = box_desc.item_prod_cost + box_desc.item_transport_cost + box_desc.item_other_cost
		all_bom_op_cost += bom_op_cost

	for order in prod_entries:
		box_desc = frappe.get_doc("CM Box Description", order.box_desc)
		bom_op_cost = box_desc.item_prod_cost + box_desc.item_transport_cost + box_desc.item_other_cost

		planned_rm_cost = order.planned_rm_cost * order.mfg_qty
		act_rm_cost = order.act_rm_cost * order.mfg_qty
		planned_op_cost = bom_op_cost * order.mfg_qty
		act_op_cost = act_indirect_cost * bom_op_cost/all_bom_op_cost

		op_profit = (planned_op_cost - act_op_cost)
		planned_cost = planned_op_cost + planned_rm_cost
		act_cost = act_op_cost + act_rm_cost

		#prod_order = frappe.get_doc("CM Production Order", order.name)
		#paper_qty = prod_order.get_used_paper_qty()

		sales_price = frappe.db.get_value("Item", order.box, "standard_rate") * order.mfg_qty
		int_loss = 0
		profit = ((sales_price - act_cost - int_loss) * 100)/act_cost

		if (consolidated):
			entry = next((entry for entry in result if entry[0] == order.box), None)
			if (entry is not None):
				print("Updating entry for {0}".format(order.box))
				entry[1] += planned_rm_cost
				entry[2] += act_rm_cost
				entry[3] += op_profit
				entry[4] += planned_cost
				entry[7] = (entry[7] * entry[5] + profit * act_cost)/(entry[5] + act_cost)
				entry[5] += act_cost
				entry[6] += sales_price
			else:
				result.append([order.box, planned_rm_cost, act_rm_cost, op_profit, planned_cost, act_cost, sales_price, profit])
		else:
			result.append([order.box, order.mfg_date, order.name, planned_rm_cost, act_rm_cost, op_profit, planned_cost, act_cost, sales_price, profit])

	#result.append(["", "", "", "", "", "", "", "","",""])

	return result

def get_columns(consolidated):
	columns = [_("Box Name") + ":Link/Item:150"]
	if (not consolidated):
		columns += [_("Production Date") + ":Date:120", _("Production") + ":Link/CM Production Order:200"]
	columns += [_("BOM Material Cost") + ":Currency:100", _("Actual Material Cost") + ":Currency:100",
			 _("Operating Profit") + ":Currency:100", _("Planned Cost") + ":Currency:100", _("Actual Cost") + ":Currency:100",
			  _("Sales Cost") + ":Currency:100", _("Profit") + ":Percent:100"]
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
		expense = frappe.get_doc("Journal Entry", expense_entry.name)
		#print("{0}    {1}".format(expense.title, expense.total_debit))
		expense_total += expense.total_debit

	return expense_total

def get_chart_data(columns, data, consolidated):
	data_idx = 3 if not consolidated else 1
	data = sorted(data, key=lambda x: x[data_idx + 5])
	x_intervals = ['x'] + [d[0] for d in data]

	rm_profit, op_proft, total_profit = [], [], []

	for d in data:
		rm_profit.append(d[data_idx] - d[data_idx+1])
		op_proft.append(d[data_idx + 2])
		total_profit.append(d[data_idx + 5] - d[data_idx + 4])

	columns = [x_intervals]
	columns.append(["RM Profit"] + rm_profit)
	columns.append(["OP Profit"] + op_proft)
	columns.append(["Total Profit"] + total_profit)

	chart = {
		"data": {
			'x': 'x',
			'columns': columns,
			'colors': {
				'RM Profit': 'Brown',
				'OP Profit': 'Blue',
				'Total Profit': 'Green'
			}
		}
	}

	chart["chart_type"] = "line"

	return chart
