// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Box Management', {
	setup: function(frm) {
		frm.get_field('box_profit_items').grid.editable_fields = [
				{fieldname: 'box', columns: 2},
				{fieldname: 'board', columns: 2},
				{fieldname: 'papers', columns: 2},
				{fieldname: 'box_rate', columns: 2},
				{fieldname: 'profit', columns: 2},
			];
		frm.get_field('box_capacity_items').grid.editable_fields = [
				{fieldname: 'box', columns: 2},
				{fieldname: 'box_desc', columns: 2},
				{fieldname: 'papers', columns: 4},
				{fieldname: 'mfg_qty', columns: 2},
			];
	},
	invoke_doc_function(frm, method) {
		frappe.call({
			doc: frm.doc,
			method: method,
			callback: function(r) {
				if(!r.exe) {
					frm.refresh_fields();
				}
			}
		});
	},
	onload: function(frm) {
		frm.events.mgmnt_type(frm)
	},
	mgmnt_type: function(frm) {
		frm.toggle_display("box_profit_items", frm.doc.mgmnt_type == "Profit Management")
		frm.toggle_display("box_count", frm.doc.mgmnt_type == "Profit Management")
		frm.toggle_display("paper_count", frm.doc.mgmnt_type == "Profit Management")
		frm.toggle_display("box_capacity_items", frm.doc.mgmnt_type == "Stock Management")
		if (frm.doc.mgmnt_type == "Stock Management") {
			frm.events.invoke_doc_function(frm, "populate_box_capacity");
		} else {
			frm.events.invoke_doc_function(frm, "populate_box_profit");
		}
		frm.refresh_fields();
	},
});
