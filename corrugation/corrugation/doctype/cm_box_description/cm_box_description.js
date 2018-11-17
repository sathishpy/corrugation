// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt
<<<<<<< HEAD
frappe.ui.form.on('CM Box Description', {
	setup: function(frm) {
		frm.get_field('item_papers').grid.editable_fields = [
				{fieldname: 'rm_type', columns: 2},
				{fieldname: 'rm', columns: 4},
				{fieldname: 'rm_rate', columns: 1},
				{fieldname: 'rm_weight', columns: 1},
=======
cur_frm.add_fetch("item", "item_name", "item_name");

frappe.ui.form.on('CM Box Description', {
	setup: function(frm) {
		frm.get_field('item_papers').grid.editable_fields = [
				{fieldname: 'rm_type', columns: 3},
				{fieldname: 'rm', columns: 5},
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
				{fieldname: 'rm_cost', columns: 2}
			];
		frm.get_field('item_others').grid.editable_fields = [
				{fieldname: 'rm_type', columns: 2},
				{fieldname: 'rm', columns: 4},
<<<<<<< HEAD
				{fieldname: 'rm_rate', columns: 1},
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
=======
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
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
			};
		}
		frm.fields_dict.item_others.grid.get_field('rm').get_query = function(doc, cdt, cdn) {
			item = locals[cdt][cdn]
			group = 'Gum'
			if (item.rm_type == 'Printing Ink') {
				group = 'Ink'
<<<<<<< HEAD
			} else if (item.rm_type == 'Stitching Coil') {
				group = 'Coil'
=======
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
			}
			return {
				filters: [
					['Item', 'item_group', '=', group]
				]
			};
		}
	},
	onload: function(frm) {
<<<<<<< HEAD
		frm.add_fetch("box", "box_item", "item");
		frm.add_fetch("item", "item_name", "item_name");
		frm.add_fetch("box", "box_length", "item_length")
		frm.add_fetch("box", "box_width", "item_width")
		frm.add_fetch("box", "box_height", "item_height")
		frm.add_fetch("box", "box_ply_count", "item_ply_count")
		frm.add_fetch("box", "box_top_type", "item_top_type")
		frm.add_fetch("box", "box_rate", "item_rate")
		frm.events.update_cost(frm);
	},
	invoke_doc_function(frm, method, args = null) {
		frappe.call({
			doc: frm.doc,
			method: method,
			args: args,
			callback: function(r) {
				if(!r.exe) {
					frm.refresh_fields();
=======
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
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
				}
			}
		});
	},
<<<<<<< HEAD
	box: function(frm) {
		frm.events.invoke_doc_function(frm, "populate_raw_materials")
	},
	swap_deck: function(frm) {
		frm.events.box(frm)
	},
	refresh: function(frm) {
		frm.add_custom_button(__('Update Costs'), function() {
				frm.events.update_rate_and_cost(frm);
		});

		frm.refresh_fields();
	},
	update_rate_and_cost(frm) {
		frm.events.invoke_doc_function(frm, "update_rate_and_cost")
	},
	update_cost: function(frm) {
		frm.events.invoke_doc_function(frm, "update_cost")
	},
	item_rate : function(frm, cdt, cdn) {
		frm.events.invoke_doc_function(frm, "update_cost")
	},
	item_pin_lap : function(frm, cdt, cdn) {
		frm.events.invoke_doc_function(frm, "populate_raw_materials")
	},
	item_cutting_margin : function(frm, cdt, cdn) {
		frm.events.invoke_doc_function(frm, "populate_raw_materials")
	},
	item_per_sheet : function(frm, cdt, cdn) {
		frm.events.invoke_doc_function(frm, "populate_raw_materials")
	},
	item_per_length : function(frm, cdt, cdn) {
		frm.events.invoke_doc_function(frm, "populate_raw_materials")
	},
	item_flute : function(frm) {
		frm.events.update_cost(frm);
	},
	item_is_slotted : function(frm) {
		frm.events.update_cost(frm);
	},
	item_stitched : function(frm) {
		frm.events.invoke_doc_function(frm, "populate_misc_materials")
=======
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
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
	},
	item_prod_cost : function(frm) {
		frm.events.update_cost(frm);
	},
<<<<<<< HEAD
	item_transport_cost : function(frm) {
		frm.events.update_cost(frm);
	},
	item_other_cost : function(frm) {
		frm.events.update_cost(frm);
	},
	credit_rate : function(frm) {
		frm.events.update_cost(frm);
	},
	credit_period : function(frm) {
		frm.events.update_cost(frm);
	},
	exclude_tax : function(frm) {
		frm.events.update_rate_and_cost(frm);
	},
	scrap_ratio : function(frm) {
		frm.events.update_cost(frm);
	},
	add_new_paper(frm) {
		frappe.prompt([{fieldtype:"Data", label: __("New Paper(BF-GSM-Deck)"), fieldname:"paper", 'default': '16-180-80' },
									 {fieldtype:"Select", label: __("Colour"), fieldname:"color", 'default': 'Brown', 'options':['White', 'Brown'] }],
											function(data) {
												frm.events.invoke_doc_function(frm, "add_new_paper", {"paper": data.paper, "color": data.color})
											}, __("New Paper"), __("Add"));
	},

});
frappe.ui.form.on("CM Paper Item", "rm", function(frm, cdt, cdn) {
	row = locals[cdt][cdn]
	if (!row.rm) return
	frm.events.invoke_doc_function(frm, "update_layers", {"rm_type": row.rm_type, "rm": row.rm})
});
frappe.ui.form.on("CM Paper Item", "rm_rate", function(frm, cdt, cdn) {
	frm.events.update_cost(frm);
});
frappe.ui.form.on("CM Misc Item", "rm_type", function(frm, cdt, cdn) {
	frm.events.invoke_doc_function(frm, "update_misc_items")
});
frappe.ui.form.on("CM Misc Item", "rm", function(frm, cdt, cdn) {
	frm.events.update_rate_and_cost(frm);
});
frappe.ui.form.on("CM Misc Item", "rm_rate", function(frm, cdt, cdn) {
	frm.events.update_cost(frm);
});
frappe.ui.form.on("CM Misc Item", "rm_percent", function(frm, cdt, cdn) {
=======
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
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
	frm.events.update_cost(frm);
});
