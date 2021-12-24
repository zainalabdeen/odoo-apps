# -*- coding: utf-8 -*-


from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.exceptions import UserError
from odoo.osv import expression

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    picking_type_id = fields.Many2one('stock.picking.type')

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a stock rule
        comming from a sale order line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        self.ensure_one()
        date_planned = self.order_id.confirmation_date\
            + timedelta(days=self.customer_lead or 0.0) - timedelta(days=self.order_id.company_id.security_lead)
        values.update({
            'company_id': self.order_id.company_id,
            'group_id': group_id,
            'sale_line_id': self.id,
            'date_planned': date_planned,
            'route_ids': self.route_id,
            'picking_type_id' : self.picking_type_id,
            'warehouse_id': self.picking_type_id.warehouse_id or False,
            'partner_id': self.order_id.partner_shipping_id.id,
        })
        for line in self.filtered("order_id.commitment_date"):
            date_planned = fields.Datetime.from_string(line.order_id.commitment_date) - timedelta(days=line.order_id.company_id.security_lead)
            values.update({
                'date_planned': fields.Datetime.to_string(date_planned),
            })
        return values





class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def _search_rule(self, route_ids, product_id, warehouse_id,domain,picking_type_id=False):
        """ First find a rule among the ones defined on the procurement
        group, then try on the routes defined for the product, finally fallback
        on the default behavior
        """
        if warehouse_id:
            domain = expression.AND([['|', ('warehouse_id', '=', warehouse_id.id), ('warehouse_id', '=', False)], domain])
        Rule = self.env['stock.rule']
        res = self.env['stock.rule']
        if route_ids:
            res = Rule.search(expression.AND([[('route_id', 'in', route_ids.ids)], domain]), order='route_sequence, sequence', limit=1)
        if picking_type_id:
            res = Rule.search(expression.AND([[('picking_type_id', '=', picking_type_id.id),('route_id.sale_selectable','=',True)], domain]), order='route_sequence, sequence', limit=1)    
        if not res:
            product_routes = product_id.route_ids | product_id.categ_id.total_route_ids
            if product_routes:
                res = Rule.search(expression.AND([[('route_id', 'in', product_routes.ids)], domain]), order='route_sequence, sequence', limit=1)
        if not res and warehouse_id:
            warehouse_routes = warehouse_id.route_ids
            if warehouse_routes:
                res = Rule.search(expression.AND([[('route_id', 'in', warehouse_routes.ids)], domain]), order='route_sequence, sequence', limit=1)
        return res

    @api.model
    def _get_rule(self, product_id, location_id, values):
        """ Find a pull rule for the location_id, fallback on the parent
        locations if it could not be found.
        """
        result = False
        location = location_id
        while (not result) and location:
            domain = ['&', ('location_id', '=', location.id), ('action', '!=', 'push')]
            # In case the method is called by the superuser, we need to restrict the rules to the
            # ones of the company. This is not useful as a regular user since there is a record
            # rule to filter out the rules based on the company.
            if self.env.user._is_superuser() and values.get('company_id'):
                domain_company = ['|', ('company_id', '=', False), ('company_id', 'child_of', values['company_id'].ids)]
                domain = expression.AND([domain, domain_company])
            result = self._search_rule(values.get('route_ids', False), product_id, values.get('warehouse_id', False), domain,values.get('picking_type_id',False))
            location = location.location_id
        return result        