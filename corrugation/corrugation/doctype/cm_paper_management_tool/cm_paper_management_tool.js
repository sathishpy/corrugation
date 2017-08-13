// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Paper Management Tool', {
	setup: function(frm) {
		frm.get_field('paper_rates').grid.editable_fields = [
				{fieldname: 'colour', columns: 2},
				{fieldname: 'bf', columns: 2},
				{fieldname: 'gsm', columns: 2},
				{fieldname: 'std_rate', columns: 2},
				{fieldname: 'landing_rate', columns: 2}
			];
		frm.get_field('new_papers').grid.editable_fields = [
				{fieldname: 'colour', columns: 3},
				{fieldname: 'bf_gsm_deck', columns: 4},
				{fieldname: 'paper', columns: 3},
			];
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
	refresh: function(frm) {
		frm.add_custom_button(__('Update Rate'), function() {
				frm.events.invoke_doc_function(frm, "update_paper_rate");
		});
		frm.add_custom_button(__('Add Paper'), function() {
				frm.events.invoke_doc_function(frm, "add_new_paper");
		});
	},
});

frappe.ui.form.on("CM New Paper Item", "bf_gsm_deck", function(frm, cdt, cdn) {
	frm.events.invoke_doc_function(frm, "check_paper");
});
