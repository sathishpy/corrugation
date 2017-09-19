// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Paper Management', {
	setup: function(frm) {
		frm.get_field('paper_rates').grid.editable_fields = [
				{fieldname: 'colour', columns: 2},
				{fieldname: 'bf', columns: 2},
				{fieldname: 'gsm', columns: 2},
				{fieldname: 'std_rate', columns: 2},
				{fieldname: 'landing_rate', columns: 2}
			];
		frm.get_field('new_papers').grid.editable_fields = [
				{fieldname: 'colour', columns: 3},
				{fieldname: 'bf_gsm_deck', columns: 4},
				{fieldname: 'paper', columns: 3},
			];
		frm.get_field('paper_to_boxes').grid.editable_fields = [
				{fieldname: 'paper', columns: 2},
				{fieldname: 'box_count', columns: 4},
				{fieldname: 'boxes', columns: 3},
				{fieldname: 'paper_qty', columns: 1},
			];
	},
	invoke_doc_function(frm, method) {
		frappe.call({
			doc: frm.doc,
			method: method,
			callback: function(r) {
				if(!r.exe) {
					frm.refresh_fields();
				}
			}
		});
	},
	refresh: function(frm) {
	},
	onload: function(frm) {
		frm.events.mgmnt_type(frm)
	},
	update_rate: function(frm) {
		frm.events.invoke_doc_function(frm, "update_paper_rate");
	},
	add_paper: function(frm) {
		frm.events.invoke_doc_function(frm, "add_new_paper");
	},
	sort_on_deck: function(frm) {
		frm.events.invoke_doc_function(frm, "sort_on_deck");
	},
	sort_on_box_count: function(frm) {
		frm.events.invoke_doc_function(frm, "sort_on_box_count");
	},
	sort_on_weight: function(frm) {
		frm.events.invoke_doc_function(frm, "sort_on_weight");
	},
	mgmnt_type: function(frm) {
		frm.toggle_display("sb_paper_rate", frm.doc.mgmnt_type == "Update Rate")
		frm.toggle_display("sb_new_paper", frm.doc.mgmnt_type == "New Paper")
		frm.toggle_display("sb_paper_to_box", frm.doc.mgmnt_type == "Paper Box Mapping")
		frm.toggle_display("sb_paper_to_box_fns", frm.doc.mgmnt_type == "Paper Box Mapping")
		if (frm.doc.mgmnt_type == "Paper Box Mapping") {
			frm.events.invoke_doc_function(frm, "map_paper_to_boxes");
		}
		frm.refresh_fields();
	},
	box_filter: function(frm) {
		frm.events.invoke_doc_function(frm, "filter_boxes");
	},
});

frappe.ui.form.on("CM New Paper Item", "bf_gsm_deck", function(frm, cdt, cdn) {
	frm.events.invoke_doc_function(frm, "check_paper");
});
