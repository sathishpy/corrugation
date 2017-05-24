// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Product Costs', {
	setup: function(frm) {
		frm.get_field('product_cost').grid.editable_fields = [
				{fieldname: 'cm_product', columns: 2},
				{fieldname: 'cm_bom_cost', columns: 2},
				{fieldname: 'cm_actual_cost', columns: 2}
			];
	},
	refresh: function(frm) {

	}
});
