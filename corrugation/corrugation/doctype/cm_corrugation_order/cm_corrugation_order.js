// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Corrugation Order', {
	setup: function(frm) {
		frm.get_field('paper_rolls').grid.editable_fields = [
				{fieldname: 'rm_type', columns: 1},
				{fieldname: 'paper_roll', columns: 4},
				{fieldname: 'start_weight', columns: 2},
				{fieldname: 'est_weight', columns: 1},
				{fieldname: 'final_weight', columns: 2}
			];
		frm.events.set_sales_order_filter(frm)
		frm.events.set_box_filter(frm)
		frm.events.set_box_desc_filter(frm)
		frm.events.set_roll_filter(frm)
	},

	onload: function(frm) {
		if (frm.doc.docstatus != 1) {
			frm.set_value("mfg_date", frappe.datetime.nowdate())
			frm.add_fetch("box_desc", "sheet_length", "sheet_length")
			frm.add_fetch("box_desc", "sheet_width", "sheet_width")
		} else {
			frm.set_df_property("mfg_qty", "read_only", 1);
		}
	},

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

	set_sales_order_filter: function(frm) {
		frm.fields_dict['sales_order'].get_query = function(doc, dt, dn) {
			return {
				filters:[
					["Sales Order", "status", "in", ["Draft", "To Deliver and Bill"]]
				]
			}
		};
	},

	set_box_filter: function(frm) {
		frm.set_query("box", function(doc) {
			if (!doc.sales_order) return
			return {
				query: "corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order.get_sales_order_items",
				filters: {
								"sales_order": doc.sales_order,
							},
			};
		});
	},

	set_box_desc_filter: function(frm) {
		frm.set_query("box_desc", function(doc) {
			if (doc.box) {
				return {
					filters:[
						['CM Box Description', 'item', '=', doc.box]
					]
				}
			} else msgprint(__("Please select the Item first"));
		});
	},

	set_roll_filter: function(frm) {
		frm.fields_dict.paper_rolls.grid.get_field('paper_roll').get_query = function(doc, cdt, cdn) {
			row = locals[cdt][cdn]
			return {
				query: "corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order.filter_rolls",
				filters: {
									'box_desc': doc.box_desc,
									'layer_type': row.rm_type,
									'ignore_bom': frm.doc.ignore_bom,
								},
			};
		}
	},

	refresh: function(frm) {
		if (frm.doc.docstatus == 1) {
			frm.add_custom_button(__('Update Board Count'), function() {
					frm.events.update_prod_qty(frm)
			});
			frm.add_custom_button(__('Make Other Layer'), function() {
					frm.events.make_other_layer(frm)
			});
			frm.add_custom_button(__('Update Costs'), function() {
					frm.events.invoke_function(frm, "update_production_cost")
			});
		}
	},

	sales_order: function(frm) {
		frm.events.invoke_function(frm, "populate_order_items")
	},
	box: function(frm) {
		frm.events.invoke_function(frm, "populate_item_prod_info")
	},
	auto_populate: function(frm) {
		frm.events.invoke_function(frm, "populate_rolls")
	},
	clear_rolls: function(frm) {
		frm.doc.paper_rolls = []
		frm.refresh_fields()
	},
	layer_type: function(frm) {
		frm.events.invoke_function(frm, "update_layer")
	},
	make_other_layer: function(frm) {
		frappe.model.open_mapped_doc({
			method: "corrugation.corrugation.doctype.cm_corrugation_order.cm_corrugation_order.make_other_layer",
			frm: frm,
		})
	},
	update_prod_qty(frm) {
		if (frm.doc.docstatus != 1) return
		frappe.prompt({fieldtype:"Int", label: __("Updated board quantity"), fieldname:"qty", 'default': frm.doc.mfg_qty },
			function(data) {
				frappe.call({
					doc: frm.doc,
					method:"update_production_quantity",
					args: {"qty": data.qty},
					callback: function(r) {
						frm.refresh_fields()
					}
				});
			}, __("Updated Quantity"), __("Update"));
	},
});
frappe.ui.form.on("CM Production Roll Detail", "paper_roll", function(frm, cdt, cdn) {
	frappe.call({
		doc: frm.doc,
		method: "update_box_roll_qty",
		callback: function(r) {
			if(!r.exe) {
				refresh_field("paper_rolls");
			}
		}
	});
});
frappe.ui.form.on("CM Production Roll Detail", "rm_type", function(frm, cdt, cdn) {
	row = locals[cdt][cdn]
	if (frm.layer_type == "Top" && row.rm_type != "Top") {
		msgprint("Roll type doesn't match the layer type")
	}
	if (frm.layer_type == "Flute" && row.rm_type == "Top") {
		msgprint("Roll type doesn't match the layer type")
	}
});

frappe.ui.form.on("CM Production Roll Detail", "paper_rolls_add", function(frm, cdt, cdn) {
	frappe.call({
		doc: frm.doc,
		method: "set_new_layer_defaults",
		callback: function(r) {
			if(!r.exe) {
				refresh_field("paper_rolls");
			}
		}
	});
});
