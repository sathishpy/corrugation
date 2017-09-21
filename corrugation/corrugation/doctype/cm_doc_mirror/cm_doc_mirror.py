# -*- coding: utf-8 -*-
# Copyright (c) 2017, sathishpy@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.frappeclient import FrappeClient
import json
from time import sleep

class CMDocMirror(Document):
	def autoname(self):
		self.name = "DocMirror" + self.mirror_type

	def send_mirror_data(self, item):
		client = FrappeClient(self.mirror_url, self.username, self.get_password(fieldname="password", raise_exception=False))
		print("Calling remote mirror_document on {0} to mirror {1}:{2}".format(client.url, item.doc_type, item.doc_method))

		result = client.post_request({
						"cmd": "corrugation.corrugation.doctype.cm_doc_mirror.cm_doc_mirror.mirror_document",
						"seq_no": item.seq_no,
						"method": item.doc_method,
						"doc": json.dumps(item.doc, default=date_handler)
					})
		print("Result of remote request is {0}".format(result))
		return int(result)

	def process_mirroring_request(self, item):
		import datetime
		doc_dict = eval(item.doc)

		if (frappe.db.get_value(doc_dict["doctype"], doc_dict["name"]) is not None):
			doc = frappe.get_doc(doc_dict["doctype"], doc_dict["name"])
		else:
			doc = frappe.new_doc(doc_dict["doctype"])
		doc.update(doc_dict)

		mock = False
		if ("localhost" in self.mirror_url): mock = True
		if (item.doc_method == "on_update"):
			print("Updating item {0}-{1}".format(item.doc_type, item.doc_name))
			if not mock: doc.save()
		elif (item.doc_method == "on_submit"):
			print("Submitting item {0}-{1}".format(item.doc_type, item.doc_name))
			if not mock: doc.submit()
		elif (item.doc_method == "on_delete"):
			print("Deleting item {0}-{1}".format(item.doc_type, item.doc_name))
			if not mock: doc.delete()
		elif (item.doc_method == "on_cancel"):
			print("Cancelling item {0}-{1}".format(item.doc_type, item.doc_name))
			if not mock: doc.cancel()
		return item.seq_no

	def mirror_queued_items(self, process_method):
		ack = idx = 0
		for idx in range(0, len(self.doc_items)):
			item = self.doc_items[idx]
			print("{0}: Mirroring item {1}:{2}({3})".format(self.mirror_type, item.doc_type, item.doc_name, item.seq_no))
			try:
				ack = process_method(item)
				if (ack > self.ack_seq):
					self.ack_seq = ack
				if (ack == item.seq_no):
					self.move_doc_item_to_mirrored_list(item)
				self.save()
			except Exception as e:
				print("{0}:Received exception - {1}".format(self.mirror_type, e))
				print("{0}:Failed to process doc - {1}".format(self.mirror_type, item.doc))

	def release_lock(self):
		print("{0}: releasing table lock".format(self.mirror_type))
		frappe.db.set_value(self.doctype, self.name, "lock", 0)

	def mirror_pending_items(self):
		try:
			if (self.mirror_type == "Sender"):
				self.mirror_queued_items(self.send_mirror_data)
			elif (self.mirror_type == "Receiver"):
				self.mirror_queued_items(self.process_mirroring_request)
		except:
			pass

	def move_doc_item_to_mirrored_list(self, item):
		print("{1}: Moving item {0}:{2} to mirrored queue".format(item.seq_no, self.mirror_type, item.doc_name))
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

	def send_mirror_item(self, method, doc):
		self.add_item_to_mirror_queue(self.mirror_seq, method, doc)
		frappe.enqueue("corrugation.corrugation.doctype.cm_doc_mirror.cm_doc_mirror.mirror_doc_updates")

	def receive_mirror_item(self, seq_no, method, doc):
		#don't accept seq_no that we are not anticipating
		#if (int(seq_no) > self.mirror_seq):
		#	print("Out of order sequence no {0} received, expected: {1}".format(seq_no, self.mirror_seq))
		#	return 0
		self.add_item_to_mirror_queue(seq_no, method, doc)
		frappe.enqueue("corrugation.corrugation.doctype.cm_doc_mirror.cm_doc_mirror.apply_doc_updates")
		print("Returning sequence no {0} for {1}".format(seq_no, self.mirror_seq))
		return seq_no

	def add_item_to_mirror_queue(self, seq_no, method, doc):
		item = next((item for item in self.doc_items if item.doc_name == doc["name"] and item.doc_type == doc["doctype"] and item.doc_method == method), None)
		if (item is not None and (item.seq_no == seq_no or item.doc == doc)):
			print("{0}: Duplicate item {1}:{2} with seq_no {3} ignored".format(self.mirror_type, item.doc_type, item.doc_name, item.seq_no))
			return
		self.mirror_seq += 1
		item = frappe.new_doc("CM Doc Mirror Item")
		item.seq_no = seq_no
		item.doc_type = doc["doctype"]
		item.doc_name = doc["name"]
		item.doc_method = method
		item.doc = doc
		self.append("doc_items", item)

		try:
			self.save()
			print("{0}: Added item {1}:{2} (seq:{3}) to mirror queue".format(self.mirror_type, item.doc_type, item.doc_name, item.seq_no))
		except Exception as e:
			print ("Got Exception {0}".format(e))

	def load_default_docs(self):
		default_mon_events = {"Item": "on_update, after_delete",
								 "Item Group": "on_update, after_delete",
#								 "Item Price": "on_update",
								 "CM Box": "on_update, after_delete",
								 "CM Box Description": "on_update, on_submit, on_cancel",
								 "Customer": "on_update, after_delete",
								 "Supplier": "on_update, after_delete",
								 "Address": "on_update, after_delete",
								 "Purchase Order": "on_submit, on_cancel",
								 "Sales Order": "on_submit, on_cancel",
								 "Purchase Receipt": "on_submit, on_cancel",
								 "Purchase Invoice": "on_submit, on_cancel",
								 "Sales Invoice": "on_submit, on_cancel",
#								 "Delivery Note": "on_submit, on_cancel",
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

def get_locked_mirror_doc(doc_name):
	if (frappe.db.get_value("CM Doc Mirror", doc_name) is None): return

	alarm, timeout = 0, 20
	lock = int(frappe.db.get_value("CM Doc Mirror", doc_name, "lock"))
	print("{0}: Acquiring lock {1}".format(doc_name, lock))
	while (lock == 1 and alarm < timeout):
		sleep(0.05)
		alarm += 1
		lock = int(frappe.db.get_value("CM Doc Mirror", doc_name, "lock"))

	frappe.db.set_value("CM Doc Mirror", doc_name, "lock", 1)
	lock = int(frappe.db.get_value("CM Doc Mirror", doc_name, "lock"))
	if (alarm >= timeout):
		print("{0}: Acquired lock({1}) due to timeout".format(doc_name, lock))
	else:
		print("{0}: locked({1}) table".format(doc_name, lock))
	return frappe.get_doc("CM Doc Mirror", doc_name)

def add_doc_to_mirroring_queue(doc, method):
	if (frappe.db.get_value("CM Doc Mirror", "DocMirrorSender") is None): return

	ignore_list = ["CM Doc Mirror", "Communication", "DocType", "Version", "Error Log", "Authentication Log"]
	for doctype in ignore_list:
		if doctype in doc.doctype: return

	#print("Attempting to mirror item {0}:{1} for method {2}".format(doc.doctype, doc.name, method))
	mirror_doc = frappe.get_doc("CM Doc Mirror", "DocMirrorSender")
	monitored_item_events = {}
	for doc_item in mirror_doc.documents:
		monitored_item_events[doc_item.doc_type] = doc_item.doc_methods

	if (doc.doctype not in monitored_item_events or method not in monitored_item_events[doc.doctype]): return
	doc_dict = strip_unwanted_values(doc.as_dict())
	print("Sender: Sending item {0}:{1} for method {2}".format(doc.doctype, doc.name, method))
	mirror_doc = get_locked_mirror_doc("DocMirrorSender")
	mirror_doc.send_mirror_item(method, doc_dict)
	mirror_doc.release_lock()

@frappe.whitelist()
def mirror_document(seq_no, method, doc):
	if (frappe.db.get_value("CM Doc Mirror", "DocMirrorReceiver") is None):
		return
	from six import string_types
	if not isinstance(doc, string_types):
		print("Receiver: Received unknown mirror request for {0} {1}".format(seq_no, method))
		return

	doc_map = json.loads(doc)
	if isinstance(doc, unicode):
		import datetime
		doc_map = eval(doc_map)
	doc_map = strip_unwanted_values(frappe._dict(doc_map))
	print("Receiver: Received mirror request({0}) for {1}:{2}".format(seq_no, doc_map["doctype"], doc_map["name"]))
	mirror_doc = get_locked_mirror_doc("DocMirrorReceiver")
	seq_no = mirror_doc.receive_mirror_item(seq_no, method, doc_map)
	mirror_doc.release_lock()
	return seq_no

@frappe.whitelist()
def mirror_doc_updates():
	print("Checking pending items to mirror")
	mirror_doc = get_locked_mirror_doc("DocMirrorSender")
	if (mirror_doc is None): return
	mirror_doc.mirror_pending_items()
	mirror_doc.release_lock()

@frappe.whitelist()
def apply_doc_updates():
	print("Checking pending items updates")
	mirror_doc = get_locked_mirror_doc("DocMirrorReceiver")
	if (mirror_doc is None): return
	mirror_doc.mirror_pending_items()
	mirror_doc.release_lock()

def date_handler(obj):
	if (hasattr(obj, 'isoformat')):
		return obj.isoformat()
	else:
		raise TypeError

def strip_unwanted_values(doc_dict):
	doc_dict.pop("creation", None)
	doc_dict.pop("modified", None)
	doc_dict.pop("docstatus", None)
	for (key, value) in doc_dict.items():
		if not value:
			doc_dict.pop(key, None)
			continue
		val_type = str(type(value))
		if "dict" in val_type:
			#print("Dict Key is {0} value type={1}".format(key, val_type))
			doc_dict[key] = strip_unwanted_values(value)
		if "list" in val_type:
			#print("List Key is {0} value type={1}".format(key, val_type))
			for item in value:
				item_val_type = str(type(item))
				if "dict" in item_val_type:
					item = strip_unwanted_values(item)
	return doc_dict
