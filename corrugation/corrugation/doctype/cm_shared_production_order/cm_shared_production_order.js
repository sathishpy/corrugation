// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Shared Production Order', {
	setup: function(frm) {
		frm.get_field('cm_box_rolls').grid.editable_fields = [
				{fieldname: 'cm_rm_type', columns: 1},
				{fieldname: 'cm_paper', columns: 4},
				{fieldname: 'cm_start_weight', columns: 1},
				{fieldname: 'cm_est_final_weight', columns: 1},
				{fieldname: 'cm_final_weight', columns: 1}
			];
		frm.get_field('cm_box_details').grid.editable_fields = [
			{fieldname: 'cm_box', columns:2},
			{fieldname: 'cm_box_descr', columns:3},
			{fieldname: 'cm_planned_qty', columns:2},
			{fieldname: 'cm_prod_qty', columns:2},
		];
		frm.set_query("cm_box", "cm_box_details", function(doc, cdt, cdn) {
			return {
				filters:[
					['Item', 'item_group', '=', 'Products']
				]
			}
		})
		frm.set_query("cm_box_desc", "cm_box_details", function(doc, cdt, cdn) {
			row = locals[cdt][cdn]
			if (row.cm_box_desc) {
				return {
					filters:[
						['CM Box Description', 'item', '=', row.cm_box]
					]
				}
			} else msgprint(__("Please select the Item first"));
		});
	},
	refresh: function(frm) {

	},
	onload: function(frm) {
		frm.events.set_default_warehouse(frm);
	},
	set_default_warehouse: function(frm) {
		if (!(frm.doc.cm_source_wh || frm.doc.cm_target_wh)) {
			frappe.call({
				method: "erpnext.manufacturing.doctype.production_order.production_order.get_default_warehouse",

				callback: function(r) {
					if(!r.exe) {
						frm.set_value("cm_source_wh", r.message.wip_warehouse);
						frm.set_value("cm_target_wh", r.message.fg_warehouse)
					}
				}
			});
		}
	},


});
frappe.ui.form.on('CM Shared Production Order', {
});
