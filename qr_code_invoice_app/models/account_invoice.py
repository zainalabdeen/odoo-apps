# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api ,_
from odoo.http import request
from .qr_generator import generateQrCode
from odoo.tools import html2plaintext
import base64
from odoo.exceptions import UserError

class QRCodeInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    discount_amount = fields.Monetary(string='Discount Amount', compute='_get_discount_amount', store=True)

    @api.one
    @api.depends('price_unit', 'discount','quantity')
    def _get_discount_amount(self):
        self.discount_amount = self.price_unit * (self.discount / 100.0) * self.quantity

class QRCodeInvoice(models.Model):
    _inherit = 'account.invoice'

    qr_image = fields.Binary("QR Code", compute='_generate_qr_code')
    partner_vat = fields.Char(string='Partner Tax ID',help="The Parnter Tax Identification Number.",related='partner_id.vat',store=True)
    company_vat = fields.Char(string='Company Tax ID',related="company_id.vat",store=True, index=True, help="Your Company Tax Identification Number.")
    datetime_invoice = fields.Datetime('Confirmation DateTime',readonly=True) 
    supply_date = fields.Date()
    total_discount_amount = fields.Monetary(string='Discount Amount', compute='_get_discount_amount', store=True,track_visibility='always')
    
    @api.one
    @api.depends('invoice_line_ids.price_unit', 'invoice_line_ids.discount','invoice_line_ids.quantity')
    def _get_discount_amount(self):
        self.total_discount_amount = sum(self.invoice_line_ids.mapped('discount_amount'))


    @api.depends('company_id')
    def _generate_qr_code(self):
        qr_info = ''
        for rec in self:
            if rec.company_id.invoice_qr_type == 'by_url':
                qr_info = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                qr_info += rec.get_portal_url()
            elif rec.company_id.invoice_qr_type == 'by_info': 
                if rec.company_id.invoice_field_ids:
                    result = rec.search_read([('id', 'in', rec.ids)],
                    rec.company_id.invoice_field_ids.mapped('field_id.name'))
                    dict_result = {}   
                    for ffild in rec.company_id.invoice_field_ids.mapped('field_id'):
                        if ffild.ttype == 'many2one':
                            dict_result[ffild.field_description] = rec[ffild.name].display_name
                        elif ffild.name == 'access_url':
                            invoice_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                            invoice_url += rec.get_portal_url()
                            dict_result[ffild.field_description] = invoice_url
                        else:
                            dict_result[ffild.field_description] = rec[ffild.name]
                    for key,value in dict_result.items():
                        if str(key).__contains__('Partner') or str(key).__contains__(_('Partner')):
                            if rec.type in ['out_invoice','out_refund']:
                                key = str(key).replace(_('Partner'),_('Customer'))    
                            elif rec.type in ['in_invoice','in_refund']:
                                key = str(key).replace(_('Partner'),_('Vendor'))   
                        qr_info += f"{key} : {value} <br/>" 
                    qr_info = html2plaintext(qr_info)  
            elif rec.company_id.invoice_qr_type == 'by_encoded_info':   
                qr_info = rec._compute_qr_code_str()   
            rec.qr_image = generateQrCode.generate_qr_code(qr_info)


    def _compute_qr_code_str(self):
        """ Generate the qr code for Saudi e-invoicing. Specs are available at the following link at page 23
        https://zatca.gov.sa/ar/E-Invoicing/SystemsDevelopers/Documents/20210528_ZATCA_Electronic_Invoice_Security_Features_Implementation_Standards_vShared.pdf
        """
        def get_qr_encoding(tag, field):
            company_name_byte_array = field.encode('UTF-8')
            company_name_tag_encoding = tag.to_bytes(length=1, byteorder='big')
            company_name_length_encoding = len(company_name_byte_array).to_bytes(length=1, byteorder='big')
            return company_name_tag_encoding + company_name_length_encoding + company_name_byte_array

        for record in self:
            qr_code_str = ''
            if (record.datetime_invoice or record.create_date) and record.company_id.vat:
                seller_name_enc = get_qr_encoding(1, record.company_id.display_name)
                company_vat_enc = get_qr_encoding(2, record.company_id.vat)
                if record.datetime_invoice:
                    time_sa = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'), record.datetime_invoice)
                else:    
                    time_sa = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'), record.create_date)
                timestamp_enc = get_qr_encoding(3, time_sa.isoformat())
                invoice_total_enc = get_qr_encoding(4, str(record.amount_total))
                total_vat_enc = get_qr_encoding(5, str(record.currency_id.round(record.amount_total - record.amount_untaxed)))

                str_to_encode = seller_name_enc + company_vat_enc + timestamp_enc + invoice_total_enc + total_vat_enc
                qr_code_str = base64.b64encode(str_to_encode).decode('UTF-8')
            return qr_code_str

    @api.multi
    def action_invoice_open(self):
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        to_open_invoices.write({'datetime_invoice':fields.Datetime.now()})
        return super(QRCodeInvoice,self).action_invoice_open()

    @api.multi
    def action_cancel(self):
        res = super(QRCodeInvoice,self).action_cancel()
        for inv in self:
            inv.write({'datetime_invoice':False})
        return res    