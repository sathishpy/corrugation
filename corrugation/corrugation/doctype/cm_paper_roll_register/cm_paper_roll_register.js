// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Paper Roll Register', {
	setup: function(frm) {
		frm.get_field('charges').grid.editable_fields = [
				{fieldname: 'party', columns: 2},
				{fieldname: 'from_account', columns: 3},
				{fieldname: 'to_account', columns: 3},
				{fieldname: 'amount', columns: 2},
		];
		frm.get_field('paper_rolls').grid.editable_fields = [
				{fieldname: 'paper', columns: 4},
				{fieldname: 'number', columns: 2},
				{fieldname: 'weight', columns: 2},
				{fieldname: 'unit_cost', columns: 2},
		];
	},
	onload: function(frm) {
		frm.add_fetch("purchase_receipt", "supplier", "supplier");
	},
	refresh: function(frm) {
		frm.add_custom_button(__('Update Price'), function() {
				frm.events.invoke_function(frm, "update_roll_cost")
		});

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
	purchase_receipt: function(frm) {
		frm.events.invoke_function(frm, "populate_rolls")
	},
});
frappe.ui.form.on("CM Paper Roll Detail", "weight", function(frm, cdt, cdn) {
	weight = 0
	frm.doc.paper_rolls.forEach(function(d) { weight += d.weight; });
	frm.set_value("total_weight", weight)
	frm.refresh_fields()
});
