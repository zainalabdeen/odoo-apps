# -*- coding: utf-8 -*-
{
    'name': "Warehouse Multi Receipts",

    'summary': """
        Allow Receipt Purchase Order In Multi Picking""",

    'description': """
        Allow Receipt Purchase Order In Multi Picking
    """,

    'author': "Zain-Alabdin",
    #'website': "http://my-company.com",
    'category': 'Purchases',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['purchase_stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/deliver_to_line.xml',
        'views/res_config_settings_views.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    "images":  ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'license': "AGPL-3",
}
