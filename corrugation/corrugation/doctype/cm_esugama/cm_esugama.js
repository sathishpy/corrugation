// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM ESugama', {
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
