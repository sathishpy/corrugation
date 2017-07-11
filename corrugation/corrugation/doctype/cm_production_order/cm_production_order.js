// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Production Order', {
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
					['Sales Order', 'status', '=', 'To Deliver and Bill']
				]
			}
		};
		frm.events.set_box_filter(frm)
	},
	onload: function(frm) {
		frm.events.set_default_warehouse(frm);
	},
	refresh: function(frm) {
		frm.add_custom_button(__('Check Production Capacity'), function() {
				msgprint("Implementation in progress")
		});
		frm.add_custom_button(__('Create Purhcase Order'), function() {
				frm.events.make_po(frm)
		});
		frm.add_custom_button(__('Create Stock Based BOM'), function() {
				msgprint("Not implemented yet")
		});
		if (frm.doc.__islocal) return;
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

	setup_company_filter: function(frm) {
		var company_filter = function(doc) {
			return {
				filters: {
					'company': frm.doc.company,
					'is_group': 0
				}
			}
		}

		frm.fields_dict.source_warehouse.get_query = company_filter;
		frm.fields_dict.target_warehouse.get_query = company_filter;
	},
	sales_order: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "populate_order_items",
			callback: function(r) {
				if(!r.exe) {
					refresh_field("box")
					refresh_field("mfg_qty")
					refresh_field("box_desc")
					frm.events.box_desc(frm)
				}
			}
		});
	},
	set_box_filter: function(frm) {
		frm.set_query("box_desc", function(doc) {
			if (doc.box) {
				return {
					filters:[
						['CM Box Description', 'item', '=', doc.box]
					]
				}
			} else msgprint(__("Please select the Item first"));
		});
	},
	box_desc: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "populate_box_rolls",
			callback: function(r) {
				if(!r.exe) {
					refresh_field("paper_rolls");
					refresh_field("bom")
				}
			}
		});
	},
	mfg_qty: function(frm) {
		frm.events.box_desc(frm)
	},
	make_po: function(frm) {
		frappe.model.open_mapped_doc({
			method: "corrugation.corrugation.doctype.cm_production_order.cm_production_order.make_new_purchase_order",
			frm: frm
		})
	}
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
