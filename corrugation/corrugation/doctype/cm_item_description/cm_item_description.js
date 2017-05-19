// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt
cur_frm.add_fetch("item", "item_name", "item_name");

frappe.ui.form.on('CM Item Description', {
	refresh: function(frm) {
		frm.add_custom_button(__('Make BOM'),
		  function() {
				frm.events.make_bom()
			});
		frm.events.update_sheet_values(frm);
	},
	make_bom: function() {
		frappe.model.open_mapped_doc({
			method: "corrugation.corrugation_manufacturing.doctype.cm_item_description.cm_item_description.make_new_bom",
			frm: cur_frm
		})
	},

	item_width : function(frm, cdt, cdn) {
		frm.events.update_sheet_values(frm);
	},
	item_length : function(frm, cdt, cdn) {
		frm.events.update_sheet_values(frm);
	},
	item_height : function(frm, cdt, cdn) {
		frm.events.update_sheet_values(frm);
	},
	item_margin : function(frm, cdt, cdn) {
		frm.events.update_sheet_values(frm);
	},
	update_sheet_values : function(frm) {
		frm.set_value("sheet_length", 2 * (frm.doc.item_width + frm.doc.item_length) + frm.doc.item_margin);
		frm.set_value("sheet_width", (frm.doc.item_width + frm.doc.item_height));
	},
});
