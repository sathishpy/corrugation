// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Tally Account Mapper', {
	setup: function(frm) {
		frm.get_field('mapped_accounts').grid.editable_fields = [
			{fieldname: 'account', columns: 4},
			{fieldname: 'tally_account', columns: 6},
		];
	},
	refresh: function(frm) {

	}
});
