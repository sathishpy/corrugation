// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Payment Manager', {
	refresh: function(frm) {

	},
	invoke_doc_function(frm, method) {
		frappe.call({
			doc: frm.doc,
			method: method,
			callback: function(r) {
				if(!r.exe) {
					frm.refresh_fields();
				}
			}
		});
	},

	get_payment_entries: function(frm) {
		frm.events.invoke_doc_function(frm, "populate_payment_entries");
	},

	match_invoices: function(frm) {
		frm.events.invoke_doc_function(frm, "populate_matching_invoices");
	},
	create_payments: function(frm) {
		frm.events.invoke_doc_function(frm, "create_payment_entries");
	},
});
