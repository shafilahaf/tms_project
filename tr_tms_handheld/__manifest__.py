# -*- coding: utf-8 -*-
{
    "name": "TR TMS Handheld",
    "author": "Trusta Technologies",
    "website": "https://trusta.co.id",
    "category": "Services/TMSHandheld",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["base"],
    # always loaded
    "data": [
        "security/tms_handheld_groups.xml",
        "security/ir.model.access.csv",
        "views/tms_company_inherit.xml",
        "views/tms_company_inherit.xml",
        "views/tms_purchase_order.xml",
        "views/tms_receipt.xml",
        "views/tms_receipt_details.xml",
        "views/tms_sales.xml",
        "views/tms_transfer.xml",
        "views/menu/tms_handheld_menu.xml",
        "views/tms_item.xml",
        "views/tms_unit_of_measures.xml",
        "views/tms_item_uom.xml",
        "views/tms_item_identifiers.xml",
        "views/tms_item_variant.xml",
        "views/tms_reservation_entry.xml",
        "views/tms_purchase_receipt.xml",
        "views/tms_purchase_scan.xml",
    ],
    "assets": {
        "web.assets_backend": [
        ],
    },
}
