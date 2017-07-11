// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Data Import Tool', {
	setup: function(frm) {
		frm.get_field('party_items').grid.editable_fields = [
			{fieldname: 'party_name', columns: 2},
			{fieldname: 'party_type', columns: 1},
			{fieldname: 'party_tin', columns: 1},
			{fieldname: 'party_address', columns:6},
		];
		frm.get_field('roll_items').grid.editable_fields = [
			{fieldname: 'paper_color', columns: 2},
			{fieldname: 'paper_bf', columns: 2},
			{fieldname: 'paper_gsm', columns: 2},
			{fieldname: 'paper_deck', columns:2},
			{fieldname: 'roll_weight', columns:2},
		];
		frm.get_field('box_items').grid.editable_fields = [
			{fieldname: 'box_name', columns: 4},
			{fieldname: 'length', columns: 1},
			{fieldname: 'width', columns: 1},
			{fieldname: 'height', columns:1},
			{fieldname: 'ply', columns:1},
			{fieldname: 'rate', columns:2},
		];
	},
	refresh: function(frm) {
		frm.add_custom_button(__('Import Data'),
	  	function() {
				frm.events.create_parties(frm)
			});
	},
	onload: function(frm) {
	},
	create_parties: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "export_data",
			callback: function(r) {
				if(!r.exe) {
					msgprint("Import Complete")
					set_route("List", "Customer")
				}
			}
		});
	},
});
