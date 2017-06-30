// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Export Data', {
	setup: function(frm) {
		frm.get_field('transaction_items').grid.editable_fields = [
				{fieldname: 'posting_date', columns: 2},
				{fieldname: 'party', columns: 4},
				{fieldname: 'voucher_type', columns: 2},
				{fieldname: 'voucher_no', columns: 1},
				{fieldname: 'voucher_amount', columns: 1},
			];
	},
	onload: function(frm) {
		frm.add_custom_button(__("Tally Export"), function() {
			frm.events.export_data(frm)
		});
		//if (frm.doc.docstatus == 0) frm.events.export_data(frm)
	},
	export_data: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "export_data",
			callback: function(r) {
				if(!r.exe) {
					refresh_field("export_data");
				}
			}
		});
	},
	refresh: function(frm) {
	}
});
