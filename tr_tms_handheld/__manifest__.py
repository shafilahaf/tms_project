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
        "views/tms_handheld_transaction.xml",
        "views/tms_handheld_transaction_scan.xml",
        "views/tms_item_journal.xml",
        "views/tms_location.xml",
        # 'views/overview.xml',
        'wizard/tms_check_stock.xml',
    ],
    "assets": {
        "web.assets_backend": [
            'tr_tms_handheld/static/src/css/tree_view.css',
            'tr_tms_handheld/static/src/scss/custom.scss',
            'tr_tms_handheld/static/src/js/bus_notification.js',
            'tr_tms_handheld/static/src/js/ZXing.js',
        ],
        'web.assets_qweb': [
            'tr_tms_handheld/static/src/xml/*.xml'
        ],
    },
}
