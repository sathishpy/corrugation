import frappe
from frappe import _

def add_records(records):
    # from erpnext/setup/setup_wizard/install_fixtures.py
    # this should be added as a function in frappe like frappe.add_records(records)
    from frappe.modules import scrub
    for r in records:
        doc = frappe.new_doc(r.get("doctype"))
        doc.update(r)
        doc.insert(ignore_permissions=True)

def add_paper_item_groups(raw_material_group):
    raw_material_group.is_group = True
    raw_material_group.save()

    records = [
        {"doctype": "Item Group", "item_group_name": _("Paper"), "is_group": 0, "parent_item_group": raw_material_group.name },
        {"doctype": "Item Group", "item_group_name": _("Gum"), "is_group": 0, "parent_item_group": raw_material_group.name },
        {"doctype": "Item Group", "item_group_name": _("Ink"), "is_group": 0, "parent_item_group": raw_material_group.name },
    ]
    print("Adding new categories to Raw Material")
    add_records(records)

def add_paper_template(name):
    frappe.db.sql("""delete from `tabItem Attribute` where name='Colour'""")
    frappe.db.sql("""delete from `tabItem Attribute Value` where parent='Colour'""")
    frappe.db.sql("""delete from `tabItem Attribute` where name='Size'""")
    frappe.db.sql("""delete from `tabItem Attribute Value` where parent='Size'""")
    records = [
        {"doctype": "Item Attribute", "attribute_name":_("BF"), "numeric_values": True, "from_range": 12, "increment": 2, "to_range": 30},
        {"doctype": "Item Attribute", "attribute_name":_("GSM"), "numeric_values": True, "from_range": 100, "increment": 20, "to_range": 250},
        {"doctype": "Item Attribute", "attribute_name":_("Deck"), "numeric_values": True, "from_range": 50, "increment": 0.5, "to_range": 250},
        {'doctype': "Item Attribute", "attribute_name": _("Colour"), "item_attribute_values": [
                                                                        {"attribute_value": _("White"), "abbr": "WHI"},
                                                                        {"attribute_value": _("Brown"), "abbr": "BRW"},]
        },
        {"doctype": "Item", "item_code": name, "item_group": "Paper", "stock_uom": "Kg", "default_material_request_type": "Purchase",
                            "is_stock_item": True, "is_fixed_asset": False, "has_variants": True, "variant_based_on": "Item Attribute",
                            "attributes": [
                                {"attribute": _("Colour")},
                                {"attribute": _("BF")},
                                {"attribute": _("GSM")},
                                {"attribute": _("Deck")},
                            ]
        },
    ]
    print("Adding paper template as Item")
    add_records(records)

def update_mf_settings():
    #Allow over production
    print "Updating manufacturing settings"
    mf_settings = frappe.get_doc({"doctype": "Manufacturing Settings", "allow_production_on_holidays": 0})
    mf_settings.allow_production_on_holidays = 1
    mf_settings.allow_overtime = 1
    mf_settings.over_production_allowance_percentage = 50
    #This doesn't handle multiple companies
    mf_settings.default_wip_warehouse = frappe.db.get_value("Warehouse", filters={"warehouse_name": _("Work In Progress")})
    mf_settings.default_fg_warehouse  = frappe.db.get_value("Warehouse", filters={"warehouse_name": _("Finished Goods")})
    mf_settings.save()

    stock_settings = frappe.get_doc({"doctype": "Stock Settings", "tolerance": 0})
    stock_settings.tolerance = 50
    stock_settings.save()

def before_install():
    update_mf_settings()

    rm_group = "Raw Material"
    paper_template = "Paper-RM"
    raw_material_group = frappe.get_doc("Item Group", rm_group)
    if (raw_material_group.is_group == False):
        add_paper_item_groups(raw_material_group)

    paper_rm = frappe.db.sql_list("""select name from `tabItem` where item_name=%s""", paper_template)
    if not paper_rm:
        add_paper_template(paper_template)

def after_install():
    doc = frappe.new_doc("CM Paper")
    doc.save(ignore_permissions=True)
