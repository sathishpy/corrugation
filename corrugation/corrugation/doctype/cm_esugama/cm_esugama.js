// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM ESugama', {
	invoke_function(frm, method) {
		frappe.call({
			doc: frm.doc,
			method: method,
			callback: function(r) {
				if(!r.exe) {
					frm.refresh_fields()
				}
			}
		});
	},

	sales_invoice: function(frm) {
		frm.events.invoke_function(frm, "populate_invoice_details")
	},

	refresh: function(frm) {
	},

	download_xml: function(frm) {
		var w = window.open("/api/method/corrugation.corrugation.doctype.cm_esugama.cm_esugama.download_xml?" +
								"invoice="+encodeURIComponent(frm.doc.sales_invoice));
		if(!w) {
            frappe.msgprint(__("Please enable pop-ups")); return;
    }
	},
});
