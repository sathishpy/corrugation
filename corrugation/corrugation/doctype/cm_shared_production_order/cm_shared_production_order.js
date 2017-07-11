// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Shared Production Order', {
	setup: function(frm) {
		frm.get_field('paper_rolls').grid.editable_fields = [
				{fieldname: 'rm_type', columns: 1},
				{fieldname: 'paper_roll', columns: 4},
				{fieldname: 'start_weight', columns: 1},
				{fieldname: 'est_final_weight', columns: 1},
				{fieldname: 'final_weight', columns: 1}
			];
		frm.get_field('box_details').grid.editable_fields = [
			{fieldname: 'sales_order', columns:2},
			{fieldname: 'box', columns:2},
			{fieldname: 'box_desc', columns:4},
			{fieldname: 'mfg_qty', columns:2},
		];
		frm.set_query("box", "box_details", function(doc, cdt, cdn) {
			return {
				filters:[
					['Item', 'item_group', '=', 'Products']
				]
			}
		})
		frm.set_query("box_desc", "box_details", function(doc, cdt, cdn) {
			row = locals[cdt][cdn]
			if (row.box) {
				return {
					filters:[
						['CM Box Description', 'item', '=', row.box]
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
		if (!(frm.doc.source_warehouse || frm.doc.target_warehouse)) {
			frappe.call({
				method: "erpnext.manufacturing.doctype.production_order.production_order.get_default_warehouse",

				callback: function(r) {
					if(!r.exe) {
						frm.set_value("source_warehouse", r.message.wip_warehouse);
						frm.set_value("target_warehouse", r.message.fg_warehouse)
					}
				}
			});
		}
	},
});
frappe.ui.form.on('CM Box Production Item', {
	box_desc: function(frm, cdt, cdn) {
		row = locals[cdt][cdn];
		matching = false
		frappe.call({
			doc: frm.doc,
			method: "is_matching_paper",
			args: {"item_info": row},
			callback: function(r) {
				if(!r.exe) {
					matching = r.message.Result
					if (matching == false) {
						msgprint("The item " + row.box + " doesn't share the paper sheet, so can't be produced in shared mode")
					} else {
						frappe.call({
							doc: frm.doc,
							method: "populate_rolls",
							callback: function(r) {
								if(!r.exe) {
									refresh_field("paper_rolls")
								}
							}
						});
					}
				}
			}
		});
	},
});
