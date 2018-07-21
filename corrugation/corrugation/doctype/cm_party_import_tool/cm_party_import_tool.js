// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Party Import Tool', {
	setup: function(frm) {
		frm.get_field('party_items').grid.editable_fields = [
			{fieldname: 'party_name', columns: 2},
			{fieldname: 'party_type', columns: 1},
			{fieldname: 'party_tin', columns: 1},
			{fieldname: 'party_address', columns:6},
		];
	},
	refresh: function(frm) {
		frm.add_custom_button(__('Export Data'),
	  	function() {
				frm.events.create_parties(frm)
			});
	},
	onload: function(frm) {
	},
	create_parties: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "export_parties",
			callback: function(r) {
				if(!r.exe) {
					msgprint("Export Complete")
					set_route("List", "Customer")
				}
			}
		});
	},
});
