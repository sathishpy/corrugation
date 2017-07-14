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
		frm.events.set_box_filter(frm)
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
	refresh: function(frm) {

	},
	mfg_qty: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "populate_rolls",
			callback: function(r) {
				if(!r.exe) {
					refresh_field("paper_rolls");
					refresh_field("board_name")
				}
			}
		});
	},
	layer_type: function(frm) {
		frm.events.mfg_qty(frm)
	},
});
