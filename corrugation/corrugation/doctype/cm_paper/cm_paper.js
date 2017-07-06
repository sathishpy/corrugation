// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Paper', {
	refresh: function(frm) {

	},
	onload: function(frm) {
		//Copied from erpnext.item
		frm.events.show_modal_for_item_attribute_selection(frm);
	},
	show_modal_for_item_attribute_selection: function(frm) {
		frappe.model.with_doc("Item", "Paper-RM", function(r) {
			var doc = frappe.model.get_doc("Item", "Paper-RM")
			var fields = []

			for(var i=0;i< doc.attributes.length;i++){
				var fieldtype, desc;
				var row = doc.attributes[i];
				if (row.numeric_values){
					fieldtype = "Float";
					desc = "Min Value: "+ row.from_range +" , Max Value: "+ row.to_range +", in Increments of: "+ row.increment
				}
				else {
					fieldtype = "Data";
					desc = ""
				}
				fields = fields.concat({
					"label": row.attribute,
					"fieldname": row.attribute,
					"fieldtype": fieldtype,
					"reqd": 1,
					"description": desc
				})
			}

			var d = new frappe.ui.Dialog({
				title: __("Make Variant"),
				fields: fields
			});

			d.set_primary_action(__("Make"), function() {
				var args = d.get_values();
				if(!args) return;
				frappe.call({
					method:"erpnext.controllers.item_variant.get_variant",
					args: {
						"template": doc.name,
						"args": d.get_values()
					},
					callback: function(r) {
						// returns variant item
						if (r.message) {
							var variant = r.message;
							frappe.msgprint_dialog = frappe.msgprint(__("Item Variant {0} already exists with same attributes",
								[repl('<a href="#Form/Item/%(item_encoded)s" class="strong variant-click">%(item)s</a>', {
									item_encoded: encodeURIComponent(variant),
									item: variant
								})]
							));
							frappe.msgprint_dialog.hide_on_page_refresh = true;
							frappe.msgprint_dialog.$wrapper.find(".variant-click").on("click", function() {
								d.hide();
							});
						} else {
							d.hide();
							frappe.call({
								method:"erpnext.controllers.item_variant.create_variant",
								args: {
									"item": doc.name,
									"args": d.get_values()
								},
								callback: function(r) {
									var doclist = frappe.model.sync(r.message);
									frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
								}
							});
						}
					}
				});
			});

			d.show();
			$.each(d.fields_dict, function(i, field) {

				if(field.df.fieldtype !== "Data") {
					return;
				}

				$(field.input_area).addClass("ui-front");

				var input = field.$input.get(0);
				input.awesomplete = new Awesomplete(input, {
					minChars: 0,
					maxItems: 99,
					autoFirst: true,
					list: [],
				});
				input.field = field;

				field.$input
					.on('input', function(e) {
						var term = e.target.value;
						frappe.call({
							method:"frappe.client.get_list",
							args:{
								doctype:"Item Attribute Value",
								filters: [
									["parent","=", i],
									["attribute_value", "like", term + "%"]
								],
								fields: ["attribute_value"]
							},
							callback: function(r) {
								if (r.message) {
									e.target.awesomplete.list = r.message.map(function(d) { return d.attribute_value; });
								}
							}
						});
					})
					.on('focus', function(e) {
						$(e.target).val('').trigger('input');
					})
			});
		});
	},
});
