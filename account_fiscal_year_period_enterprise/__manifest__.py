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
    #'website': "www.my-company.com",

    'category': 'Invoicing Management',
    'version': '0.3',

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
    #'license': "AGPL-3",
}
