# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from erpnext.controllers.item_variant import create_variant
from erpnext.controllers.item_variant import get_variant


def schedule_daily_jobs():
    if (frappe.db.get_value("CM Box Management", "Box Management") is None): return
    print("Populating box stock items")
    box_mgmnt = frappe.get_doc("CM Box Management", "Box Management")
    box_mgmnt.populate_box_capacity()

def delete_submitted_document(doctype, docname):
    if (docname is None): return
    doc = frappe.get_doc(doctype, docname)
    if (doc.docstatus == 1):
        print("Deleting submitted document {0}:{1}".format(doctype, docname))
        doc.cancel()
    doc.delete()

def set_sales_terms(inv, method):
    if (inv.tc_name is not None): return
    terms = frappe.db.get_value("Terms and Conditions", filters={"name": "Sales Terms"})
    inv.tc_name = terms
    from erpnext.setup.doctype.terms_and_conditions.terms_and_conditions import get_terms_and_conditions
    inv.terms = get_terms_and_conditions(terms, inv.as_dict())

@frappe.whitelist()
def create_new_paper(bf_gsm_deck, color):
    attributes = bf_gsm_deck.strip().split("-")
    if (len(attributes) != 3):
        frappe.throw("Argument isn't in the right format(BF-GSM-Deck)")
    args = {"Colour": color, "BF": attributes[0], "GSM": attributes[1], "Deck": attributes[2]}
    if (get_variant("PPR", args) != None):
        frappe.throw("Paper {0} is already present".format(new_paper.bf_gsm_deck))
    print("Creating the new paper {0}".format(args))
    paper = create_variant("PPR", args)
    paper.save()
    paper_mgmnt = frappe.get_doc("CM Paper Management", "Paper Management")
    paper_mgmnt.update_paper_rate()
    return paper.name
