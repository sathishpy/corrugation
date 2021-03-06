// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt
frappe.ui.form.on('CM Box Description', {
	setup: function(frm) {
		frm.get_field('item_papers').grid.editable_fields = [
				{fieldname: 'rm_type', columns: 2},
				{fieldname: 'rm', columns: 4},
				{fieldname: 'rm_rate', columns: 1},
				{fieldname: 'rm_weight', columns: 1},
				{fieldname: 'rm_cost', columns: 2}
			];
		frm.get_field('item_others').grid.editable_fields = [
				{fieldname: 'rm_type', columns: 2},
				{fieldname: 'rm', columns: 4},
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
			};
		}
		frm.fields_dict.item_others.grid.get_field('rm').get_query = function(doc, cdt, cdn) {
			item = locals[cdt][cdn]
			group = 'Gum'
			if (item.rm_type == 'Printing Ink') {
				group = 'Ink'
			} else if (item.rm_type == 'Stitching Coil') {
				group = 'Coil'
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
				}
			}
		});
	},
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
	},
	item_prod_cost : function(frm) {
		frm.events.update_cost(frm);
	},
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
	frm.events.update_cost(frm);
});
