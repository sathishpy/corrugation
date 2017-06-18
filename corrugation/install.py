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
    add_records(records)

def add_paper_template(name):
    records = [
        {"doctype": "Item Attribute", "attribute_name":_("GSM"), "numeric_values": True, "from_range": 100, "increment": 20, "to_range": 220},
        {"doctype": "Item Attribute", "attribute_name":_("BF"), "numeric_values": True, "from_range": 12, "increment": 2, "to_range": 20},
        {"doctype": "Item Attribute", "attribute_name":_("Deck"), "numeric_values": True, "from_range": 50, "increment": 1, "to_range": 200},
        {"doctype": "Item Attribute", "attribute_name": _("Supplier"), "item_attribute_values": [
                {"attribute_value": _("Mangalore"), "abbr": "MLR"},
                {"attribute_value": _("Shimogga"), "abbr": "SMG"},
                {"attribute_value": _("Mysore"), "abbr": "MSR"},
        ]},
        {"doctype": "Item", "item_code": name, "item_group": "Paper", "stock_uom": "Kg", "default_material_request_type": "Purchase",
                            "is_stock_item": True, "is_fixed_asset": False, "has_variants": True, "variant_based_on": "Item Attribute",
                            "attributes": [
                                {"attribute": _("Colour")},
                                {"attribute": _("GSM")},
                                {"attribute": _("BF")},
                                {"attribute": _("Deck")},
                                {"attribute": _("Supplier")},
                            ]
        },
    ]
    add_records(records)


def before_install():
    rm_group = "Raw Material"
    paper_template = "Paper-RM"
    raw_material_group = frappe.get_doc("Item Group", rm_group)
    if (raw_material_group.is_group == False):
        add_paper_item_groups(raw_material_group)

    paper_rm = frappe.db.sql_list("""select name from `tabItem` where item_name=%s""", paper_template)
    if not paper_rm:
        add_paper_template(paper_template)
