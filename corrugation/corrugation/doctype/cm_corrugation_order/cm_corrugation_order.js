// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Corrugation Order', {
	setup: function(frm) {
		frm.get_field('paper_rolls').grid.editable_fields = [
				{fieldname: 'rm_type', columns: 1},
				{fieldname: 'paper_roll', columns: 4},
				{fieldname: 'start_weight', columns: 2},
				{fieldname: 'est_final_weight', columns: 1},
				{fieldname: 'final_weight', columns: 2}
			];
		frm.fields_dict['sales_order'].get_query = function(doc, dt, dn) {
			return {
				filters:[
					["Sales Order", "status", "in", ["Draft", "To Deliver and Bill"]]
				]
			}
		};
		frm.events.set_box_filter(frm)
		frm.events.set_roll_filter(frm)
	},

	onload: function(frm) {
		frm.set_value("mfg_date", frappe.datetime.nowdate())
	},

	set_box_filter: function(frm) {
		frm.set_query("box_desc", function(doc) {
			if (doc.box) {
				return {
					filters:[
						['CM Box Description', 'item', '=', doc.box]
					]
				}
			} else msgprint(__("Please select the Box first"));
		});
	},
	set_roll_filter: function(frm) {
		frm.fields_dict.paper_rolls.grid.get_field('paper_roll').get_query = function(doc, cdt, cdn) {
			row = locals[cdt][cdn]
			return {
				query: "corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order.filter_rolls",
				filters: {
									'box_desc': doc.box_desc,
									'layer_type': row.rm_type,
								},
			};
		}
	},
	refresh: function(frm) {

	},
	sales_order: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "populate_order_items",
			callback: function(r) {
				if(!r.exe) {
					frm.refresh_fields()
					frm.events.mfg_qty(frm)
				}
			}
		});
	},
	mfg_qty: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "populate_rolls",
			callback: function(r) {
				if(!r.exe) {
					frm.refresh_fields()
				}
			}
		});
	},
	manual_entry: function(frm) {
		frm.events.mfg_qty(frm)
	},
	layer_type: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "update_layer",
			callback: function(r) {
				if(!r.exe) {
					frm.refresh_fields()
				}
			}
		});
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
frappe.ui.form.on("CM Production Roll Detail", "rm_type", function(frm, cdt, cdn) {
	row = locals[cdt][cdn]
	if (frm.layer_type == "Top" && row.rm_type != "Top") {
		msgprint("Roll type doesn't match the layer type")
	}
	if (frm.layer_type == "Flute" && row.rm_type == "Top") {
		msgprint("Roll type doesn't match the layer type")
	}
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
