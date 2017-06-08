// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Production Order', {
	setup: function(frm) {
		frm.get_field('cm_box_rolls').grid.editable_fields = [
				{fieldname: 'cm_paper', columns: 2},
				{fieldname: 'cm_start_weight', columns: 2},
				{fieldname: 'cm_final_weight', columns: 2}
			];
		frm.fields_dict['sales_order'].get_query = function(doc, dt, dn) {
			return {
				filters:[
					['Sales Order', 'status', '=', 'To Deliver and Bill']
				]
			}
		}
		frm.add_fetch("CM Paper Roll", "cm_weight", "cm_start_weight");
	},
	refresh: function(frm) {

	},
	sales_order: function(frm) {
		frm.fields_dict['cm_item'].get_query = function(doc, dt, dn) {
			return {
				filters:[
					['Item', 'total_projected_qty', '<', '0']
				]
			}
		}
	},
	cm_item: function(frm) {
		frm.set_query("cm_box_detail", function(doc) {
			if (doc.cm_item) {
				return {
					filters:[
						['CM Box Description', 'item', '=', doc.cm_item]
					]
				}
			} else msgprint(__("Please select the Item first"));
		});
	},
	cm_box_detail: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "populate_box_rolls",
			callback: function(r) {
				if(!r.exe) {
					refresh_field("cm_box_rolls");
				}
			}
		});
	}
});
