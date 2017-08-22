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
		if (frm.doc.mgmnt_type == "Update Rate") {
			frm.add_custom_button(__('Update Rate'), function() {
					frm.events.invoke_doc_function(frm, "update_paper_rate");
			});
		}
		if (frm.doc.mgmnt_type == "New Paper") {
			frm.add_custom_button(__('Add Paper'), function() {
					frm.events.invoke_doc_function(frm, "add_new_paper");
			});
		}
		if (frm.doc.mgmnt_type == "Paper Box Mapping") {
			frm.add_custom_button(__('Sort On Weight'), function() {
				frm.events.invoke_doc_function(frm, "sort_on_weight");
			});
			frm.add_custom_button(__('Sort On Box Count'), function() {
				frm.events.invoke_doc_function(frm, "sort_on_box_count");
			});
			frm.add_custom_button(__('Sort On Deck'), function() {
				frm.events.invoke_doc_function(frm, "sort_on_deck");
			});
		}
	},
	onload: function(frm) {
		frm.events.mgmnt_type(frm)
	},
	mgmnt_type: function(frm) {
		frm.toggle_display("paper_rates", frm.doc.mgmnt_type == "Update Rate")
		frm.toggle_display("new_papers", frm.doc.mgmnt_type == "New Paper")
		frm.toggle_display("paper_to_boxes", frm.doc.mgmnt_type == "Paper Box Mapping")
		if (frm.doc.mgmnt_type == "Paper Box Mapping") {
			frm.events.invoke_doc_function(frm, "map_paper_to_boxes");
		}
		frm.refresh_fields();
	},
});

frappe.ui.form.on("CM New Paper Item", "bf_gsm_deck", function(frm, cdt, cdn) {
	frm.events.invoke_doc_function(frm, "check_paper");
});
