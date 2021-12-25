# -*- coding: utf-8 -*-
{
    'name': "Account Fiscal Year Period Enterprise",

    'summary': """
    Create periods Of Fiscal Year Per Month ,With Ability To Open/Close Each Month
    """,

    'description': 
    """
        Create periods Of Fiscal Year Per Month With Ability To Open/Close Each Month
    """
    ,

    'author': "Zain-Alabdin",
    'website': "https://www.linkedin.com/in/zainalabdeen-merghani-56b7ab106",

    'category': 'Invoicing Management',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['account_accountant'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'data/account_fiscal_sequence.xml'
    ],
    # only loaded in demonstration mode
    'demo': [],
    "images":  ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'license': "Other proprietary"
}
