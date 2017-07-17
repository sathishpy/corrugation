// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Shared Corrugation Order', {
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
		frm.set_query("sales_order", "box_details", function(doc, cdt, cdn) {
			return {
				filters:[
					["Sales Order", "status", "in", ["Draft", "To Deliver and Bill"]]
				]
			}
		});
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
	onload: function(frm) {
		frm.set_value("mfg_date", frappe.datetime.nowdate())
	},
	refresh: function(frm) {

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
	manual_entry: function(frm) {
		frm.events.populate_rolls(frm);
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
frappe.ui.form.on('CM Shared Corrugation Item', {
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

frappe.ui.form.on("CM Production Roll Detail", "paper_roll", function(frm, cdt, cdn) {
	frappe.call({
		doc: frm.doc,
		method: "update_box_roll_qty",
		callback: function(r) {
			if(!r.exe) {
				refresh_field("paper_rolls");
			}
		}
	});
});
frappe.ui.form.on("CM Production Roll Detail", "paper_rolls_add", function(frm, cdt, cdn) {
	frappe.call({
		doc: frm.doc,
		method: "set_new_layer_defaults",
		callback: function(r) {
			if(!r.exe) {
				refresh_field("paper_rolls");
			}
		}
	});
});
