// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Corrugation Tracker', {
	setup: function(frm) {
		frm.get_field('cm_paper_rolls').grid.editable_fields = [
				{fieldname: 'cm_item', columns: 2},
				{fieldname: 'cm_weight', columns: 2},
				{fieldname: 'cm_final_weight', columns: 2}
			];
	},
	refresh: function(frm) {

	}
});
