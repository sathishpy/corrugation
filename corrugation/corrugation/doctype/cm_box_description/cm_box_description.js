// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt
cur_frm.add_fetch("item", "item_name", "item_name");

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
		frm.fields_dict['item'].get_query = function(doc, dt, dn) {
			return {
				filters:[
					['Item', 'item_group', '=', 'Products']
				]
			}
		}
		frm.fields_dict.item_papers.grid.get_field('rm').get_query = function(doc, cdt, cdn) {
			return {
				filters: [
					['Item', 'item_group', '=', 'Paper']
				]
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
		frm.add_custom_button(__("Create Parties"), function() {
			frm.events.create_parties(frm)
		});

		if (!frm.doc.__islocal) return;
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
		if (frm.doc.__islocal) return;
		frm.events.update_sheet_values(frm);
	},
	make_bom: function(curfrm) {
		frappe.model.open_mapped_doc({
			method: "corrugation.corrugation.doctype.cm_box_description.cm_box_description.make_new_bom",
			frm: curfrm
		})
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
	item_width : function(frm, cdt, cdn) {
		frm.events.update_sheet_values(frm);
	},
	item_length : function(frm, cdt, cdn) {
		frm.events.update_sheet_values(frm);
	},
	item_height : function(frm, cdt, cdn) {
		frm.events.update_sheet_values(frm);
	},
	item_margin : function(frm, cdt, cdn) {
		frm.events.update_sheet_values(frm);
	},
	item_per_sheet : function(frm, cdt, cdn) {
		frm.events.update_sheet_values(frm);
	},
	item_ply_count : function(frm, cdt, cdn) {
		frm.events.update_sheet_values(frm);
		frappe.call({
			doc: frm.doc,
			method: "populate_paper_materials",
			callback: function(r) {
				if(!r.exe) {
					frm.events.refresh_fields(frm);
				}
			}
		});
	},
	item_prod_cost : function(frm) {
		frm.events.update_cost(frm);
	},
	update_sheet_values : function(frm) {
		let sheet_length = 2 * (frm.doc.item_width + frm.doc.item_length) + frm.doc.item_pin_lap
		let sheet_width = frm.doc.item_per_sheet * (frm.doc.item_width + frm.doc.item_height + frm.doc.item_fold_lap)
		frm.set_value("sheet_length", sheet_length);
		frm.set_value("sheet_width", sheet_width);
		frm.events.update_cost(frm);
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
