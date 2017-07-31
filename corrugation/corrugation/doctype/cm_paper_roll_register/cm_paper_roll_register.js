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
				{fieldname: 'paper', columns: 5},
				{fieldname: 'number', columns: 2},
				{fieldname: 'weight', columns: 3},
		];
	},
	purchase_receipt: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "populate_rolls",
			callback: function(r) {
				if(!r.exe) {
					frm.refresh_fields()
				}
			}
		});
	},
});
frappe.ui.form.on("CM Paper Roll Detail", "weight", function(frm, cdt, cdn) {
	weight = 0
	frm.doc.paper_rolls.forEach(function(d) { weight += d.weight; });
	frm.set_value("total_weight", weight)
	frm.refresh_fields()
});
