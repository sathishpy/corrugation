// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt
frappe.ui.form.on('CM Box Description', {
	setup: function(frm) {
		frm.get_field('item_papers').grid.editable_fields = [
				{fieldname: 'rm_type', columns: 3},
				{fieldname: 'rm', columns: 5},
				{fieldname: 'rm_cost', columns: 2}
			];
		frm.get_field('item_others').grid.editable_fields = [
				{fieldname: 'rm_type', columns: 2},
				{fieldname: 'rm', columns: 4},
				{fieldname: 'rm_percent', columns: 2},
				{fieldname: 'rm_cost', columns: 2}
			];
		frm.fields_dict.item_papers.grid.get_field('rm').get_query = function(doc, cdt, cdn) {
			row = locals[cdt][cdn]
			return {
				query: "corrugation.corrugation.doctype.cm_box_description.cm_box_description.filter_papers",
				filters: {
									'sheet_length': doc.sheet_length,
									'sheet_width': doc.sheet_width,
									'top_type': doc.item_top_type,
									'layer_type': row.rm_type,
								},
			};
		}
		frm.fields_dict.item_others.grid.get_field('rm').get_query = function(doc, cdt, cdn) {
			item = locals[cdt][cdn]
			group = 'Gum'
			if (item.rm_type == 'Printing Ink') {
				group = 'Ink'
			}
			return {
				filters: [
					['Item', 'item_group', '=', group]
				]
			};
		}
	},
	onload: function(frm) {
		frm.add_fetch("box", "box_item", "item");
		frm.add_fetch("item", "item_name", "item_name");
		frm.add_fetch("box", "box_length", "item_length")
		frm.add_fetch("box", "box_width", "item_width")
		frm.add_fetch("box", "box_height", "item_height")
		frm.add_fetch("box", "box_ply_count", "item_ply_count")
		frm.add_fetch("box", "box_top_type", "item_top_type")
		frm.add_fetch("box", "box_rate", "item_rate")
	},
	box: function(frm) {
		frm.events.update_sheet_values(frm)
		frappe.call({
			doc: frm.doc,
			method: "populate_raw_materials",
			callback: function(r) {
				if(!r.exe) {
					refresh_field("item_papers");
					refresh_field("item_others");
				}
			}
		});
	},
	refresh: function(frm) {
		frm.events.refresh_fields(frm);
	},
	update_cost: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "update_cost",
			callback: function(r) {
				if(!r.exe) {
					frm.events.refresh_fields(frm);
				}
			}
		});
	},
	item_pin_lap : function(frm, cdt, cdn) {
		frm.events.update_sheet_values(frm)
		frm.events.update_cost(frm);
	},
	item_fold_lap : function(frm, cdt, cdn) {
		frm.events.update_sheet_values(frm)
		frm.events.update_cost(frm);
	},
	item_per_sheet : function(frm, cdt, cdn) {
		frm.events.update_sheet_values(frm)
		frm.events.update_cost(frm);
	},
	item_flute : function(frm) {
		frm.events.update_cost(frm);
	},
	item_prod_cost : function(frm) {
		frm.events.update_cost(frm);
	},
	update_sheet_values : function(frm) {
		let sheet_length = 2 * (frm.doc.item_width + frm.doc.item_length) + frm.doc.item_pin_lap
		let sheet_width = frm.doc.item_per_sheet * (frm.doc.item_width + frm.doc.item_height + frm.doc.item_fold_lap)
		frm.set_value("sheet_length", sheet_length);
		frm.set_value("sheet_width", sheet_width);
	},
	refresh_fields : function(frm) {
		refresh_field("item_papers");
		refresh_field("item_others");
		refresh_field("item_rm_cost");
		refresh_field("item__cost");
		refresh_field("item_total_cost");
		refresh_field("item_profit");
	},
});
frappe.ui.form.on("CM Paper Item", "rm", function(frm, cdt, cdn) {
	frm.events.update_cost(frm);
});
frappe.ui.form.on("CM Misc Item", "rm", function(frm, cdt, cdn) {
	frm.events.update_cost(frm);
});
