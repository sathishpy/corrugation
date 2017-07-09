// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Box', {
	refresh: function(frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("Update Description"), function() {
				frappe.call({
					doc: frm.doc,
					method: "save",
					callback: function(r) {
						if(!r.exe) {
							frappe.route_options = {"box": frm.doc.box_name}
							frappe.set_route("List", "CM Box Description")
						}
					}
				});
			});
		}

	},
});
