// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Product Costs', {
	setup: function(frm) {
		frm.get_field('product_cost').grid.editable_fields = [
				{fieldname: 'cm_product', columns: 2},
				{fieldname: 'cm_date', columns: 2},
				{fieldname: 'cm_bom_cost', columns: 1},
				{fieldname: 'cm_act_cost', columns: 1},
				{fieldname: 'cm_profit', columns: 1}
			];
	},
	refresh: function(frm) {

	},
	onload: function(frm) {
		let date = new Date();
		let months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];
		frm.set_value("cm_year", date.getFullYear());
		frm.set_value("cm_month", months[date.getMonth() - 1])

		frappe.call({
			doc: frm.doc,
			method: "updateCosts",
			callback: function(r) {
				if(!r.exe) {
					refresh_field("cm_est_direct_cost");
					refresh_field("cm_act_direct_cost");
					refresh_field("cm_total_production");
					refresh_field("product_cost")
				}
			}
		});

	},
	cm_month: function(frm) {
		frm.events.onload(frm);
	}
});
