// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Production Order', {
	setup: function(frm) {
		frm.get_field('cm_box_rolls').grid.editable_fields = [
				{fieldname: 'cm_paper', columns: 2},
				{fieldname: 'cm_start_weight', columns: 2},
				{fieldname: 'cm_est_final_weight', columns: 2},
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
	onload: function(frm) {
		frm.events.set_default_warehouse(frm);
	},
	refresh: function(frm) {
		if (frm.doc.__islocal) return;
		frm.add_custom_button(__('Make'),
	  	function() {
				frm.events.make_pe(frm)
			});
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

	setup_company_filter: function(frm) {
		var company_filter = function(doc) {
			return {
				filters: {
					'company': frm.doc.company,
					'is_group': 0
				}
			}
		}

		frm.fields_dict.cm_source_wh.get_query = company_filter;
		frm.fields_dict.cm_target_wh.get_query = company_filter;
	},
	sales_order1: function(frm) {
		frm.fields_dict['cm_item'].get_query = function(doc, dt, dn) {
			return {
				filters:[
					['Item', 'total_projected_qty', '<', '0']
				]
			}
		}
	},
	sales_order: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "get_all_order_items",
			callback: function(r) {
				if(!r.exe) {
					if (r.message.length == 1) {
						frm.set_value("cm_item", r.message[0].item_code)
						frm.set_value("cm_planned_qty", r.message[0].qty)
					} else {
						frm.set_value("cm_item", r.message) //XXX
					}
					refresh_field("cm_item")
					refresh_field("cm_planned_qty")
					frm.events.cm_item(frm)
				}
			}
		});
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
					refresh_field("cm_bom")
				}
			}
		});
	},
	make_pe: function(frm) {
		frappe.model.open_mapped_doc({
			method: "corrugation.corrugation.doctype.cm_production_order.cm_production_order.make_new_pe",
			frm: frm
		})
	}
});
