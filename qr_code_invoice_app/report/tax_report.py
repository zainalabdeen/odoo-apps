# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api

class ReportInvoiceZakatAndTaxAuthority(models.AbstractModel):
    _name = 'report.qr_code_invoice_app.report_invoice_zakat_tax_authority'
    _description = 'Account report According To Zakat And Tax Authority'

    @api.model
    def _get_report_values(self, docids, data=None):
        #with_context(lang=o.partner_id.lang)
        return {
            'doc_ids': docids,
            'doc_model': 'account.invoice',
            'docs': self.env['account.invoice'].browse(docids),
            'report_type': data.get('report_type') if data else '',
            'user_lang':self.env.user.lang
        }