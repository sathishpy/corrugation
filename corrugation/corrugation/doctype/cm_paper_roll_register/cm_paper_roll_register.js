// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Paper Roll Register', {
	setup: function(frm) {
		frm.get_field('cm_paper_rolls').grid.editable_fields = [
				{fieldname: 'cm_item', columns: 2},
				{fieldname: 'cm_weight', columns: 2},
			];
	},
	refresh: function(frm) {
		frm.refresh_field("cm_paper_rolls")
		frm.refresh_field("cm_purchase_weight")
		frm.refresh_field("cm_total_weight")
	},
	cm_purchase_invoice: function(frm) {
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
frappe.ui.form.on("CM Paper Roll Detail", "cm_weight", function(frm, cdt, cdn) {
	weight = 0
	frm.doc.cm_paper_rolls.forEach(function(d) { weight += d.cm_weight; });
	frm.set_value("cm_total_weight", weight)
	refresh_field("cm_purchase_weight")
	refresh_field("cm_total_weight")
});
