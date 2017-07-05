// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Paper', {
	refresh: function(frm) {

	},
	onload: function(frm) {
		//frappe.set_route("Form", "Item", "Paper-RM");
		var paper = frappe.model.get_new_doc("Item")
		frappe.set_route('Form', 'Item', paper.name)
	}
});
