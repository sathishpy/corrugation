# Copyright (c) 2013, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import datetime
import calendar
from frappe import _


def execute(filters=None):
	columns = get_columns()
	entries = get_result(filters)
	#for entry in entries:
	#	print entry

	return columns, entries

def get_result(filters=None):
	print filters

	start_date = filters.get("from_date")
	end_date = filters.get("to_date")

	act_indirect_cost = get_total_expenses(start_date, end_date)
	total_planned_rm_cost = total_act_rm_cost = total_op_profit = total_planned_cost = total_act_cost = 0
	total_paper_qty = total_production = all_bom_op_cost = 0
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

		sales_price = frappe.db.get_value("Item", order.box, "standard_rate") * order.mfg_qty
		int_loss = 0
		profit = ((sales_price - act_cost - int_loss) * 100)/act_cost

		total_planned_rm_cost += planned_rm_cost
		total_act_rm_cost += act_rm_cost
		total_op_profit += op_profit
		total_planned_cost += planned_cost
		total_act_cost += act_cost
		total_production += sales_price

		result.append([order.box, order.mfg_date, order.name, planned_rm_cost, act_rm_cost, 0, op_profit, planned_cost, act_cost, profit])

	total_profit = ((total_production - total_act_cost) * 100 / total_act_cost)
	result.append(["", "", "", "", "", "", "", "","",""])
	result.append(["Total", "", "", total_planned_rm_cost, total_act_rm_cost, 0, total_op_profit, total_planned_cost, total_act_cost, total_profit])

	return result

def get_columns():
	columns = [
			_("Box Name") + ":Link/Item:150", _("Production Date") + ":Date:120", _("Production") + ":Link/CM Production Order:150",
			_("BOM Material Cost") + ":Currency:100", _("Actual Material Cost") + ":Currency:100",
			_("Paper Quantity") + ":Float:100", _("Operating Profit") + ":Currency:100",
			_("Planned Cost") + ":Currency:100", _("Actual Cost") + ":Currency:100",
			  _("Profit") + ":Float:100",
			]
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
