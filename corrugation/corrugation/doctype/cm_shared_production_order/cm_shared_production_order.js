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
		frm.set_query("box_desc", "box_details", function(doc, cdt, cdn) {
			row = locals[cdt][cdn]
			if (row.box) {
				return {
					filters:[
						['CM Box Description', 'item', '=', row.box]
					]
				}
			} else frappe.msgprint(__("Please select the Item first"));
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
	populate_rolls: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "populate_rolls",
			callback: function(r) {
				if(!r.exe) {
					refresh_field("paper_rolls")
				}
			}
		});
	},
	check_and_populate_rolls: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "is_compatible_bom",
			callback: function(r) {
				if(!r.exe) {
					matching = r.message.Result
					if (matching == false) {
						frappe.msgprint("The item doesn't share the paper sheet, so can't be produced in shared mode")
					} else {
						frm.events.populate_rolls(frm)
					}
				}
			}
		});
	}
});
frappe.ui.form.on('CM Shared Production Item', {
	sales_order: function(frm, cdt, cdn) {
		row = locals[cdt][cdn];
		frappe.call({
			doc: frm.doc,
			method: "populate_order_items",
			args: {"item_info": row},
			callback: function(r) {
				if(!r.exe) {
					refresh_field("box_details")
					frm.events.check_and_populate_rolls(frm)
				}
			}
		})
	},
	box_desc: function(frm) {
		frm.events.check_and_populate_rolls(frm)
	},
	mfg_qty: function(frm, cdt, cdn) {
		frm.events.populate_rolls(frm)
	},
});
