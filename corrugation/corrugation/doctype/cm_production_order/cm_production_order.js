// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Production Order', {
	setup: function(frm) {
		frm.get_field('paper_rolls').grid.editable_fields = [
			  {fieldname: 'rm_type', columns: 1},
				{fieldname: 'paper_roll', columns: 4},
				{fieldname: 'start_weight', columns: 2},
				{fieldname: 'est_weight', columns: 1},
				{fieldname: 'final_weight', columns: 2}
			];
		frm.get_field('paper_boards').grid.editable_fields = [
			  {fieldname: 'layer_type', columns: 2},
				{fieldname: 'layer', columns: 4},
				{fieldname: 'stock_qty', columns: 2},
				{fieldname: 'used_qty', columns: 2},
			];
		frm.get_field('crg_orders').grid.editable_fields = [
			  {fieldname: 'crg_order', columns: 6},
				{fieldname: 'board_count', columns: 4},
			];
		frm.events.set_sales_order_filter(frm)
		frm.events.set_box_filter(frm)
		frm.events.set_box_desc_filter(frm)
		frm.events.set_roll_filter(frm)
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
				filters: {'sales_order': doc.sales_order},
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
		};
		frm.fields_dict.paper_boards.grid.get_field('layer').get_query = function(doc, cdt, cdn) {
			row = locals[cdt][cdn]
			return {
				query: "corrugation.corrugation.doctype.cm_production_order.cm_production_order.filter_boards",
				filters: {
									'box_desc': doc.box_desc,
									'layer_type': row.layer_type,
									'ignore_bom': doc.ignore_bom,
								},
			};
		}
	},

	onload: function(frm) {
		if (frm.doc.docstatus != 1) {
			frm.set_value("mfg_date", frappe.datetime.nowdate())
		} else {
			frm.set_df_property("mfg_qty", "read_only", 1);
		}
	},

	refresh: function(frm) {
		frm.add_custom_button(__('Update Box Count'), function() {
				frm.events.update_prod_qty(frm)
		});
		frm.add_custom_button(__('Create Purhcase Order'), function() {
				frm.events.make_purchase_order(frm)
		});
		frm.events.show_boards(frm)
	},

	sales_order: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "populate_order_items",
			callback: function(r) {
				if(!r.exe) {
					frm.refresh_fields()
					frm.events.use_boards(frm)
				}
			}
		});
	},
	box: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "populate_item_prod_info",
			callback: function(r) {
				if(!r.exe) {
					frm.refresh_fields()
					frm.events.box_desc(frm)
				}
			}
		});
	},
	box_desc: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "populate_box_source",
			callback: function(r) {
				if(!r.exe) {
					frm.refresh_fields()
				}
			}
		});
	},

	mfg_qty: function(frm) {
		frm.events.box_desc(frm)
	},
	show_boards: function(frm) {
		frm.toggle_display("manual_entry", !frm.doc.use_boards)
		frm.toggle_display("paper_rolls", !frm.doc.use_boards)
		frm.toggle_display("paper_boards", frm.doc.use_boards)
		frm.refresh_fields()
	},
	use_boards: function(frm) {
		frm.events.show_boards(frm)
		frm.events.box_desc(frm)
	},

	manual_entry: function(frm) {
		frm.toggle_display("ignore_bom", frm.doc.manual_entry)
		frm.set_value("ignore_bom", 0)
		if (frm.doc.manual_entry) {
			frm.doc.paper_rolls = []
			frm.refresh_fields()
		} else {
			frm.events.box_desc(frm)
		}
	},

	make_purchase_order: function(frm) {
		frappe.model.open_mapped_doc({
			method: "corrugation.corrugation.doctype.cm_production_order.cm_production_order.make_new_purchase_order",
			frm: frm
		})
	},
	make_sales_invoice: function(frm) {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
			frm: frm.doc.sales_order,
		})
	},
	update_prod_qty(frm) {
		if (frm.doc.docstatus != 1) return
		frappe.prompt({fieldtype:"Int", label: __("Updated box quantity"), fieldname:"qty", 'default': frm.doc.mfg_qty },
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

frappe.ui.form.on("CM Production Board Detail", "layer", function(frm, cdt, cdn) {
	frappe.call({
		doc: frm.doc,
		method: "update_board_qty",
		callback: function(r) {
			if(!r.exe) {
				refresh_field("paper_boards");
			}
		}
	});
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
