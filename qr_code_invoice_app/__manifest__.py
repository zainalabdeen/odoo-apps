# -*- coding: utf-8 -*-
{
    'name': 'QR Code Invoice App',
    'version': '1.0',
    'category': 'Accounting',
    'author': 'Zain-Alabdin',
    'summary': 'Generate QR Code for Invoice',
    #'website': 'http://www.my-company.com',
    'description': """
    -Configuration For Qr Code Type (Url,Text Information)
    -For Url It Will Open Invoice In Portal.
    -For Text Information , You Must Specify Invoice Field's To Show.
    -Add Qr Code In Invoice Form View.
    -Add Qr Code In Invoice Report.
    """,
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/account_invoice_report_template.xml',
        'views/res_config_settings_views.xml',
        'views/qr_code_invoice_view.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'license': "AGPL-3",
}