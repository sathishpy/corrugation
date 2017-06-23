// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Paper Roll Register', {
	setup: function(frm) {
		frm.get_field('paper_rolls').grid.editable_fields = [
				{fieldname: 'paper', columns: 5},
				{fieldname: 'number', columns: 2},
				{fieldname: 'weight', columns: 3},
			];
	},
	refresh: function(frm) {
		frm.refresh_field("paper_rolls")
		frm.refresh_field("purchase_weight")
		frm.refresh_field("total_weight")
	},
	purchase_receipt: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "populate_rolls",
			callback: function(r) {
				if(!r.exe) {
					frm.events.refresh(frm)
				}
			}
		});
	},
});
frappe.ui.form.on("CM Paper Roll Detail", "weight", function(frm, cdt, cdn) {
	weight = 0
	frm.doc.paper_rolls.forEach(function(d) { weight += d.weight; });
	frm.set_value("total_weight", weight)
	refresh_field("purchase_weight")
	refresh_field("total_weight")
});
