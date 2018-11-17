// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Paper Roll', {
	refresh: function(frm) {
<<<<<<< HEAD
		frm.add_custom_button(__('Scrap Paper'), function() {
				frm.events.scrap_paper(frm)
		});
	},
	scrap_paper(frm) {
		frappe.prompt({fieldtype:"Float", label: __("Amount of paper(kg) to scrap"), fieldname:"qty", 'default': frm.doc.weight },
			function(data) {
				frappe.call({
					doc: frm.doc,
					method:"scrap_paper",
					args: {"qty": data.qty},
					callback: function(r) {
						frm.refresh_fields()
					}
				});
			}, __("Scrap Paper Quantity"), __("Scarp Paper"));
	},
=======

	}
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
});
