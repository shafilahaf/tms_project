# -*- coding: utf-8 -*-
{
    'name': "Web Style Custom",

    'summary': """""",

    'description': """
    """,

    'author': "Boyke Budi Pratama",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Web',
    'version': '15.0',

    # any module necessary for this one to work correctly
    'depends': ['web'],

    # always loaded
    "assets": {
        "web.assets_backend": [
            "/web_style_custom/static/src/scss/web_custom.scss",            
        ],        
    },
    # only loaded in demonstration mode
}
