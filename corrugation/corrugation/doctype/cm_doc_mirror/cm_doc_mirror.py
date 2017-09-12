# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.frappeclient import FrappeClient
import json

class CMDocMirror(Document):
	def autoname(self):
		self.name = "DocMirror" + self.mirror_type

	def mirror_data(self, item):
		client = FrappeClient(self.mirror_url, self.username, self.get_password(fieldname="password", raise_exception=False))
		if (self.mirror_type == "Mock"): return item.seq_no
		result = 0
		print("Connecting to {0} to execute {1}:{2}".format(self.mirror_url, item.doc_type, item.doc_method))
		if (item.doc_method == "on_update"):
			doc = frappe.get_doc(item.doc_type, item.doc_name)
			result = client.update(doc.as_dict())
		elif (item.doc_method == "on_submit"):
			doc = frappe.get_doc(item.doc_type, item.doc_name)
			result = client.submit(doc.as_dict())
		elif (item.doc_method == "on_delete"):
			result = client.delete(item.doc_type, item.doc_name)
		elif (item.doc_method == "on_cancel"):
			result = client.cancel(item.doc_type, item.doc_name)
		print("Result is {0}".format(result))
		return item.seq_no if (result == 0) else 0

	def send_mirror_data(self, item):
		client = FrappeClient(self.mirror_url, self.username, self.get_password(fieldname="password", raise_exception=False))
		doc = frappe.get_doc(item.doc_type, item.doc_name)
		print("Calling remote mirror_document on {0} to mirror {1}:{2}".format(client.url, item.doc_type, item.doc_method))
		result = client.post_request({
						"cmd": "corrugation.corrugation.doctype.cm_doc_mirror.cm_doc_mirror.mirror_document",
						"seq_no": item.seq_no,
						"method": item.doc_method,
						"doc": json.dumps(doc.as_dict(), default=date_handler)
					})
		print("Result of remote request is {0}".format(result))
		return int(result)

	def process_mirroring_request(self, item):
		if (item.doc_method == "on_update"):
			print("Updating item {0}-{1}".format(item.doc_type, item.doc_name))
			item.doc.save()
		elif (item.doc_method == "on_submit"):
			print("Submitting item {0}-{1}".format(item.doc_type, item.doc_name))
			item.doc.submit()
		elif (item.doc_method == "on_delete"):
			print("Deleting item {0}-{1}".format(item.doc_type, item.doc_name))
			item.doc.delete()
		elif (item.doc_method == "on_cancel"):
			print("Cancelling item {0}-{1}".format(item.doc_type, item.doc_name))
			item.doc.cancel()
		return item.seq_no

	def mirror_queued_items(self, process_method):
		items_to_sync = [item for item in self.doc_items if item.seq_no >= self.ack_seq]
		ack = idx = retry = 0
		for idx in range(0, len(items_to_sync)):
			item = items_to_sync[idx]
			print("{0}: Mirroring item {1}".format(process_method.__name__, item.seq_no))
			try:
				ack = process_method(item)
			except Exception as e:
				print("Received expection {0}".format(e))
			if (ack == item.seq_no):
				self.ack_seq += 1
				idx += 1
				retry = 0
				self.move_doc_item_to_mirrored_list(item)
			else:
				retry += 1
			if (retry > 10): break

	def mirror_pending_items(self):
		self.mirror_queued_items(self.send_mirror_data)

	def move_doc_item_to_mirrored_list(self, item):
		print("Moving item {0} to mirrored queue".format(item.seq_no))
		new_item = frappe.new_doc("CM Doc Mirrored Item")
		new_item.seq_no = item.seq_no
		new_item.doc_method = item.doc_type + ":" + item.doc_method
		new_item.doc_name = item.doc_name
		self.append("mirrored_items", new_item)
		if (len(self.mirrored_items) > 10):
			for idx in range(0, len(self.mirrored_items)):
				self.mirrored_items[idx].idx = idx
			self.remove(self.mirrored_items[0])
		self.remove(item)
		self.save()

	def send_mirror_item(self, method, doc):
		self.mirror_seq += 1
		self.add_item_to_mirror_queue(self.mirror_seq, method, doc)
		#self.mirror_queued_items(self.send_mirror_data)
		self.save()

	def receive_mirror_item(self, seq_no, method, doc):
		#don't accept seq_no that we are not anticipating
		self.add_item_to_mirror_queue(seq_no, method, doc)
		self.mirror_queued_items(self.process_mirroring_request)
		self.mirror_seq = int(seq_no) + 1
		self.save()
		return seq_no

	def add_item_to_mirror_queue(self, seq_no, method, doc):
		item = frappe.new_doc("CM Doc Mirror Item")
		item.seq_no = seq_no
		item.doc_type = doc.doctype
		item.doc_name = doc.name
		item.doc_method = method
		item.doc = doc
		print("Adding item {0} with seq_no {1} to mirror queue".format(item.doc.name, item.seq_no))
		self.append("doc_items", item)

	def load_default_docs(self):
		default_mon_events = {"Item": "on_update, after_delete",
								 "Item Group": "on_update, after_delete",
								 "Item Price": "on_update",
								 "CM Box": "on_update, after_delete",
								 "CM Box Description": "on_submit, on_cancel",
								 "Customer": "on_update, after_delete",
								 "Supplier": "on_update, after_delete",
								 "Address": "on_update, after_delete",
								 "Purchase Order": "on_submit, on_cancel",
								 "Sales Order": "on_submit, on_cancel",
								 "Purchase Receipt": "on_submit, on_cancel",
								 "Purchase Invoice": "on_submit, on_cancel",
								 "Sales Invoice": "on_submit, on_cancel",
								 "Delivery Note": "on_submit, on_cancel",
								 "Journal Entry": "on_submit, on_cancel",
								 "Payment Entry": "on_submit, on_cancel",
								 "Account": "on_update, on_delete",
								}
		self.documents = []
		for doctype, methods in default_mon_events.items():
			doc_item = frappe.new_doc("CM Doc Mirror Doc Item")
			doc_item.doc_type = doctype
			doc_item.doc_methods = methods
			self.append("documents", doc_item)
		self.save()

def add_doc_to_mirroring_queue(doc, method):
	if (frappe.db.get_value("CM Doc Mirror", "DocMirrorSender") is None): return

	ignore_list = ["CM Doc Mirror", "Communication", "DocType", "Version", "Error Log", "Authentication Log"]
	for doctype in ignore_list:
		if doctype in doc.doctype: return

	print("Attempting to mirror item {0}:{1} for method {2}".format(doc.doctype, doc.name, method))
	mirror_doc = frappe.get_doc("CM Doc Mirror", "DocMirrorSender")
	monitored_item_events = {}
	for doc_item in mirror_doc.documents:
		monitored_item_events[doc_item.doc_type] = doc_item.doc_methods

	if (doc.doctype not in monitored_item_events or method not in monitored_item_events[doc.doctype]): return
	print("mirroring item {0}:{1} for method {2}".format(doc.doctype, doc.name, method))
	mirror_doc.send_mirror_item(method, doc)

@frappe.whitelist()
def mirror_document(seq_no, method, doc):
	print("Received mirror request for {0} {1}".format(seq_no, method))
	if (frappe.db.get_value("CM Doc Mirror", "DocMirrorReceiver") is None):
		return
	mirror_doc = frappe.get_doc("CM Doc Mirror", "DocMirrorReceiver")
	from six import string_types
	if isinstance(doc, string_types):
		doc = json.loads(doc)

	doc_obj = frappe.new_doc(doc["doctype"])
	doc_obj.update(doc)
	return mirror_doc.receive_mirror_item(seq_no, method, doc_obj)

def date_handler(obj):
	if (hasattr(obj, 'isoformat')):
		return obj.isoformat()
	else:
		raise TypeError
