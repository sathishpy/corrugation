// Copyright (c) 2016, sathishpy@gmail.com and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["CM Tally Export"] = {
	"filters": [
			{
							"fieldname":"from_date",
							"label": __("From Date"),
							"fieldtype": "Date",
							"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			},
			{
							"fieldname":"to_date",
							"label": __("To Date"),
							"fieldtype": "Date",
							"default": frappe.datetime.get_today(),
			}
	],
	onload: function(report) {
		report.page.add_menu_item(__("Export To Tally"), function() {
				msgprint("Still working on this, wait for some more time");
				frappe.call({
					method: "corrugation.corrugation.report.cm_tally_export.cm_tally_export.export_data",
					frm: report
				})
		});
	}
}
