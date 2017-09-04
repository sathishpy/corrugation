// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Doc Mirror', {
	setup: function(frm) {
		frm.get_field('doc_items').grid.editable_fields = [
				{fieldname: 'seq_no', columns: 1},
				{fieldname: 'doc_type', columns: 4},
				{fieldname: 'doc_name', columns: 2},
				{fieldname: 'doc_method', columns: 1},
			];
		frm.get_field('mirrored_items').grid.editable_fields = [
				{fieldname: 'seq_no', columns: 1},
				{fieldname: 'doc_method', columns: 1},
				{fieldname: 'doc_name', columns: 2},
			];
	},
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
	},
});
