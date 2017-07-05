// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Box', {
	refresh: function(frm) {

	},
	on_update_after_submit: function(frm) {
		msgprint("In on_update_after_submit")
		set_route("Form", "CM Box Description", frm.document.box_name)
	}
});
