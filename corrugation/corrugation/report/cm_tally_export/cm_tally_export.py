# Copyright (c) 2013, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, cstr
from frappe import _

def execute(filters=None):
    columns = get_columns(filters)
    entries = get_result(filters)
    for entry in entries:
        print entry

    return columns, entries

def get_columns(filters):
    columns = [
            _("Posting Date") + ":Date:90", _("Account") + ":Link/Account:200",
            _("Debit") + ":Float:100", _("Credit") + ":Float:100",
            _("Voucher Type") + "::120", _("Voucher No") + ":Dynamic Link/"+_("Voucher Type")+":160",
            _("Against Account") + "::120", _("Party") + "::150", _("Remarks") + "::400"
    ]

    return columns

def get_result(filters):
    group_by_condition = "group by voucher_type, voucher_no, account"
    print "Filters is {0}".format(filters)

    gl_entries = frappe.db.sql("""
        	select  posting_date, account, sum(debit) as debit, sum(credit) as credit,
                    voucher_type, voucher_no, party, against_voucher,
                    remarks, against
            from `tabGL Entry`
			where voucher_type != 'Stock Entry'
            {group_by_condition}
            order by posting_date, account""".format(group_by_condition=group_by_condition), filters, as_dict=1
	)

    return get_result_as_list(gl_entries, filters)

def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = [d.get("posting_date"), d.get("account"), d.get("debit"), d.get("credit")]

		row += [d.get("voucher_type"), d.get("voucher_no"), d.get("against"), d.get("party"),  d.get("remarks")
		]

		result.append(row)

	return result

def get_conditions(filters):
    conditions = []
    if filters.get("account"):
        lft, rgt = frappe.db.get_value("Account", filters["account"], ["lft", "rgt"])
        conditions.append("""account in (select name from tabAccount where lft>=%s and rgt<=%s and docstatus<2)""" % (lft, rgt))

    if filters.get("voucher_no"):
        conditions.append("voucher_no=%(voucher_no)s")

    if not (filters.get("account") or filters.get("party") or filters.get("group_by_account")):
        conditions.append("posting_date >=%(from_date)s")

    from frappe.desk.reportview import build_match_conditions
    match_conditions = build_match_conditions("GL Entry")
    if match_conditions: conditions.append(match_conditions)

    return "and {}".format(" and ".join(conditions)) if conditions else ""
