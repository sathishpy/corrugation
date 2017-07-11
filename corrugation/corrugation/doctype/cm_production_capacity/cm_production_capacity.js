// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Production Capacity', {
	setup: function(frm) {
		frm.get_field('rm_items').grid.editable_fields = [
			  {fieldname: 'rm_type', columns: 2},
				{fieldname: 'rm', columns: 4},
				{fieldname: 'stock_weight', columns: 2},
				{fieldname: 'capacity', columns: 2}
	},
	refresh: function(frm) {

	},
});
