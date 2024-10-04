# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
{
    "name":
    "Product Mobile Barcode Scanner | Product Mobile Barcode QRCode Scanner",
    "author":
    "Softhealer Technologies",
    "website":
    "https://www.softhealer.com",
    "support":
    "support@softhealer.com",
    "version":
    "15.0.2",
    "category":
    "Extra Tools",
    "summary":
    "Scan Barcode On Mobile, Scan Barcode In Tablet, Scan Product Mobile Barcode, Scan Product Internal Reference Number, Product Mobile Barcode Scanner, Product Mobile QRCode Scanner, Product Mobile QR Scanner Odoo",
    "description":
    """Do you want to scan Barcode or QRCode on your mobile? Do your time-wasting in product operations by manual product selection? Do you want to quickly all product prices? So here are the solutions these modules useful do quick operations of product mobile Barcode or QRCode scanner. This module used to find the product from the warehouse using scanner. You no need to select the product and do one by one. scan it and you do! So be very quick in all operations of odoo in mobile.""",
    "depends": ["sh_product_qrcode_generator", "stock"],
    "data": [
        "security/product_bm_security.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "wizard/sh_product_barcode_mobile_wizard.xml",
    ],
    "assets": {
        "web.assets_backend": [
            'sh_product_barcode_mobile/static/src/scss/custom.scss',
            'sh_product_barcode_mobile/static/src/js/bus_notification.js',
            'sh_product_barcode_mobile/static/src/js/ZXing.js'
        ]
    },
    "images": [
        "static/description/background.png",
    ],
    "live_test_url":
    "https://youtu.be/EwhzHhgxW0E",
    "installable":
    True,
    "application":
    True,
    "autoinstall":
    False,
    "price":
    50,
    "currency":
    "EUR",
    "license":
    "OPL-1"
}
