# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

def mirror_doc_updates():
    if (frappe.db.get_value("CM Doc Mirror", "DocMirrorSender") is None): return
    print("Checking pending items to mirror")
    mirror_doc = frappe.get_doc("CM Doc Mirror", "DocMirrorSender")
    mirror_doc.mirror_pending_items()

def schedule_daily_jobs():
    if (frappe.db.get_value("CM Box Management", "Box Management") is None): return
    print("Populating box stock items")
    box_mgmnt = frappe.get_doc("CM Box Management", "Box Management")
    box_mgmnt.populate_box_capacity()

def delete_submitted_document(doctype, docname):
    if (docname is None): return
    print("Deleting submitted document {0}:{1}".format(doctype, docname))
    doc = frappe.get_doc(doctype, docname)
    doc.cancel()
    doc.delete()

def set_sales_terms(inv, method):
    if (inv.tc_name is not None): return
    terms = frappe.db.get_value("Terms and Conditions", filters={"name": "Sales Terms"})
    inv.tc_name = terms
    from erpnext.setup.doctype.terms_and_conditions.terms_and_conditions import get_terms_and_conditions
    inv.terms = get_terms_and_conditions(terms, inv.as_dict())
