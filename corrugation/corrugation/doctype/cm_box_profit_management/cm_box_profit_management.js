// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Box Profit Management', {
	setup: function(frm) {
		frm.get_field('box_profit_items').grid.editable_fields = [
				{fieldname: 'box', columns: 2},
				{fieldname: 'board', columns: 2},
				{fieldname: 'papers', columns: 2},
				{fieldname: 'box_rate', columns: 2},
				{fieldname: 'profit', columns: 2},
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
		frm.add_custom_button(__('Reduce Papers'), function() {
				frm.events.invoke_doc_function(frm, "reduce_papers");
		});
	},
	onload: function(frm) {
		frm.events.invoke_doc_function(frm, "populate_boxes")
	},
});
