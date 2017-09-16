// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Doc Mirror', {
	invoke_function(frm, method) {
		frappe.call({
			doc: frm.doc,
			method: method,
			callback: function(r) {
				if(!r.exe) {
					frm.refresh_fields()
				}
			}
		});
	},

	refresh: function(frm) {
		frm.add_custom_button(__('Mirror Items'), function() {
				frm.events.invoke_function(frm, "mirror_pending_items")
		});
		frm.add_custom_button(__('Load Default Docs'), function() {
				frm.events.invoke_function(frm, "load_default_docs")
		});
	},
});
