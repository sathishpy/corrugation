// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Paper Roll Register', {
	setup: function(frm) {
		frm.get_field('cm_paper_rolls').grid.editable_fields = [
				{fieldname: 'cm_item', columns: 2},
				{fieldname: 'cm_weight', columns: 2},
			];
		frm.fields_dict['sales_order'].get_query = function(doc, dt, dn) {
			return {
				query: "erpnext.controllers.queries.sales_order_query",
				filters:{
					'status': 'Open',
				}
			}
		}
	},
	refresh: function(frm) {
		if (frm.doc.docstatus == 1) {
			frm.add_custom_button(__('Register Rolls'),
				function() {
					frm.events.register_rolls(frm)
				});
		}
	},
	cm_purchase_invoice: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "populate_rolls",
			callback: function(r) {
				if(!r.exe) {
					refresh_field("cm_paper_rolls")
				}
			}
		});
	},
	register_rolls: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "register_rolls",
			callback: function(r) {
				if(!r.exe) {
					msgprint("Paper Rolls registered")
				}
			}
		});
	}
});
