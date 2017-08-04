// Copyright (c) 2017, sathishpy@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CM Data Import Tool', {
	setup: function(frm) {
		frm.get_field('party_items').grid.editable_fields = [
			{fieldname: 'party_name', columns: 2},
			{fieldname: 'party_type', columns: 1},
			{fieldname: 'opening_balance', columns: 1},
			{fieldname: 'party_address', columns:6},
		];
		frm.get_field('account_items').grid.editable_fields = [
			{fieldname: 'account_name', columns: 3},
			{fieldname: 'account_type', columns: 2},
			{fieldname: 'mapped_account', columns:3},
			{fieldname: 'opening_balance', columns: 2},
		];
		frm.get_field('voucher_items').grid.editable_fields = [
			{fieldname: 'voucher_date', columns: 3},
			{fieldname: 'voucher_type', columns: 2},
			{fieldname: 'party', columns:3},
			{fieldname: 'voucher_amount', columns: 2},
		];
		frm.get_field('roll_items').grid.editable_fields = [
			{fieldname: 'roll_no', columns: 2},
			{fieldname: 'paper_color', columns: 2},
			{fieldname: 'paper_bf_gsm', columns: 2},
			{fieldname: 'paper_deck', columns:2},
			{fieldname: 'roll_weight', columns:2},
		];
		frm.get_field('box_items').grid.editable_fields = [
			{fieldname: 'box_name', columns: 4},
			{fieldname: 'length', columns: 1},
			{fieldname: 'width', columns: 1},
			{fieldname: 'height', columns:1},
			{fieldname: 'ply', columns:1},
			{fieldname: 'rate', columns:2},
		];
		frm.fields_dict.account_items.grid.get_field('mapped_account').get_query = function(doc, cdt, cdn) {
			row = locals[cdt][cdn]
			return {
				query: "corrugation.corrugation.doctype.cm_data_import_tool.cm_data_import_tool.filter_account",
				filters: {
									'account_name': row.account_name,
									'account_type': row.account_type,
								},
			};
		}
	},
	refresh: function(frm) {
		frm.add_custom_button(__('Extract Data'),
	  	function() {
				frm.events.call_method(frm, "extract_data")
			});
		if (frm.doc.data_type == "Account") {
			frm.add_custom_button(__('Map New Accounts'),
		  	function() {
					frm.events.call_method(frm, "map_new_accounts")
				});
		}
		frm.add_custom_button(__('Import Data'),
	  	function() {
				frm.events.import_data(frm)
			});
	},

	call_method: function(frm, method_name) {
		frappe.call({
			doc: frm.doc,
			method: method_name,
			callback: function(r) {
				if(!r.exe) {
					frm.refresh_fields()
				}
			}
		});
	},

	import_and_submit: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: "import_data",
			callback: function(r) {
				if(!r.exe) {
					msgprint("Import Complete")
				}
			}
		});
	},

	set_opening_balance: function(frm) {
		frappe.model.open_mapped_doc({
			method: "corrugation.corrugation.doctype.cm_data_import_tool.cm_data_import_tool.update_opening_balance",
			frm: frm,
		});
	},

	import_data: function(frm) {
		if (frm.doc.data_type == "Account") {
			frm.events.set_opening_balance(frm)
		} else {
			frm.events.import_and_submit(frm)
		}
	},
});
