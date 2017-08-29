# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

def delete_submitted_document(doctype, docname):
    if (docname is None): return
    doc = frappe.get_doc(doctype, docname)
    doc.cancel()
    doc.delete()
