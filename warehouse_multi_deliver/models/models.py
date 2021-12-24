# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare

from odoo.exceptions import UserError

from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase


from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    multi_deliver = fields.Boolean(string="Separate Deliver Per Line",states=Purchase.READONLY_STATES)
    deliver_line_ids = fields.One2many('deliver.to.line','order_id')

    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        if not self.multi_deliver:
            super(PurchaseOrder, self)._create_picking()
        else:
            if any([ptype in ['product', 'consu'] for ptype in self.order_line.mapped('product_id.type')]) \
            and not self.deliver_line_ids:
                raise UserError(_("Please Add Receipt Lines"))
            for picking in self.deliver_line_ids.mapped('picking_type_id'):
                if any([ptype in ['product', 'consu'] for ptype in self.deliver_line_ids.filtered(lambda s: s.picking_type_id.id== picking.id).mapped('product_id.type')]):
                    res = self._prepare_to_multi_picking(picking)
                    created_picking = StockPicking.create(res)
                    for line in self.deliver_line_ids.filtered(lambda s: s.picking_type_id.id== picking.id):
                        moves = line._create_stock_moves(created_picking)
                        moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                        seq = 0
                        for move in sorted(moves, key=lambda move: move.date_expected):
                            seq += 5
                            move.sequence = seq
                        moves._action_assign()
                        created_picking.message_post_with_view('mail.message_origin_link',
                                                   values={'self': created_picking, 'origin': line.order_id},
                                                   subtype_id=self.env.ref('mail.mt_note').id)
        return True


    @api.model
    def _prepare_to_multi_picking(self,picking_type_id):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)
        return {
            'picking_type_id': picking_type_id.id,
            'partner_id': self.partner_id.id,
            'user_id': False,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': picking_type_id.default_location_dest_id.id,
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
            }

class DeliverToLine(models.Model):
    _name = 'deliver.to.line'

    name = fields.Char()
    purchase_order_line = fields.Many2one('purchase.order.line',required=True)
    product_id = fields.Many2one('product.product',required=True,related='purchase_order_line.product_id')
    requsted_qty = fields.Integer(required=True)
    picking_type_id = fields.Many2one('stock.picking.type', 'Receipt In',required=True)
    order_id = fields.Many2one('purchase.order', string='Order Reference', index=True, required=True, ondelete='cascade')
    state = fields.Selection(related='order_id.state', store=True, readonly=False)
    move_ids = fields.One2many('stock.move', 'deliver_to_id', string='Reservation', readonly=True, ondelete='set null', copy=False)
    orderpoint_id = fields.Many2one('stock.warehouse.orderpoint', 'Orderpoint')
    qty_received = fields.Float("Received Qty", compute='_compute_qty_received', compute_sudo=True, store=True, digits='Product Unit of Measure')
    propagate_date = fields.Boolean(string="Propagate Rescheduling", help='The rescheduling is propagated to the next move.')
    propagate_date_minimum_delta = fields.Integer(string='Reschedule if Higher Than', help='The change must be higher than this value to be propagated')

    @api.onchange('purchase_order_line')
    def _onchange_purchase_order_line(self):
        self.requsted_qty = self.purchase_order_line.product_qty - self.purchase_order_line.deliver_to_qty
        self.name = self.purchase_order_line.name


    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res  
        qty = 0.0
        price_unit = self.purchase_order_line._get_stock_move_price_unit()
        outgoing_moves, incoming_moves = self._get_outgoing_incoming_moves()
        for move in outgoing_moves:
            qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.purchase_order_line.product_uom, rounding_method='HALF-UP')
        for move in incoming_moves:
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.purchase_order_line.product_uom, rounding_method='HALF-UP')
        description_picking = self.product_id.with_context(lang=self.env.user.lang)._get_description(self.picking_type_id)
        template = {
            # truncate to 2000 to avoid triggering index limit error
            # TODO: remove index in master?
            'name': (self.name or '')[:2000],
            'product_id': self.product_id.id,
            'product_uom': self.purchase_order_line.product_uom.id,
            'date': self.order_id.date_order,
            'date_expected': self.purchase_order_line.date_planned,
            'location_id': self.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': self.picking_type_id.default_location_dest_id.id,
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            #'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': self.purchase_order_line.id,
            'deliver_to_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'propagate_date': self.purchase_order_line.propagate_date,
            'propagate_date_minimum_delta': self.purchase_order_line.propagate_date_minimum_delta,
            'description_picking': description_picking,
            'propagate_cancel': self.purchase_order_line.propagate_cancel,
            'route_ids': self.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.picking_type_id.warehouse_id.id,
        }
        diff_quantity = self.requsted_qty - qty
        if float_compare(diff_quantity, 0.0,  precision_rounding=self.purchase_order_line.product_uom.rounding) > 0:
            po_line_uom = self.purchase_order_line.product_uom
            quant_uom = self.product_id.uom_id
            product_uom_qty, product_uom = po_line_uom._adjust_uom_quantities(diff_quantity, quant_uom)
            template['product_uom_qty'] = product_uom_qty
            template['product_uom'] = product_uom.id
            res.append(template)
        return res

    def _create_stock_moves(self, picking):
        values = []
        for line in self.filtered(lambda l: not l.purchase_order_line.display_type):
            for val in line._prepare_stock_moves(picking):
                values.append(val)   
        return self.env['stock.move'].create(values)

    @api.depends('move_ids.state', 'move_ids.product_uom_qty', 'move_ids.product_uom')
    def _compute_qty_received(self):
        for line in self:
                total = 0.0
                # In case of a BOM in kit, the products delivered do not correspond to the products in
                # the PO. Therefore, we can skip them since they will be handled later on.
                for move in line.move_ids.filtered(lambda m: m.product_id == line.product_id):
                    if move.state == 'done':
                        if move.location_dest_id.usage == "supplier":
                            if move.to_refund:
                                total -= move.product_uom._compute_quantity(move.product_uom_qty, line.purchase_order_line.product_uom)
                        elif move.origin_returned_move_id and move.origin_returned_move_id._is_dropshipped() and not move._is_dropshipped_returned():
                            # Edge case: the dropship is returned to the stock, no to the supplier.
                            # In this case, the received quantity on the PO is set although we didn't
                            # receive the product physically in our stock. To avoid counting the
                            # quantity twice, we do nothing.
                            pass
                        elif (
                            move.location_dest_id.usage == "internal"
                            and move.to_refund
                            and move.location_dest_id
                            not in self.env["stock.location"].search(
                                [("id", "child_of", move.warehouse_id.view_location_id.id)]
                            )
                        ):
                            total -= move.product_uom._compute_quantity(move.product_uom_qty, line.purchase_order_line.product_uom)
                        else:
                            total += move.product_uom._compute_quantity(move.product_uom_qty, line.purchase_order_line.product_uom)
                line.qty_received = total

    def _create_or_update_picking(self):
        for line in self:
            if line.product_id.type in ('product', 'consu'):
                # Prevent decreasing below received quantity
                if float_compare(line.requsted_qty, line.qty_received, line.purchase_order_line.product_uom.rounding) < 0:
                    raise UserError(_('You cannot decrease the ordered quantity below the received quantity.\n'
                                      'Create a return first.'))

                if float_compare(line.purchase_order_line.product_qty, line.purchase_order_line.qty_invoiced, line.purchase_order_line.product_uom.rounding) == -1:
                    # If the quantity is now below the invoiced quantity, create an activity on the vendor bill
                    # inviting the user to create a refund.
                    activity = self.env['mail.activity'].sudo().create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_warning').id,
                    'note': _('The quantities on your purchase order indicate less than billed. You should ask for a refund. '),
                    'res_id': line.purchase_order_line.invoice_lines[0].move_id.id,
                    'res_model_id': self.env.ref('account.model_account_move').id,
                    })
                    activity._onchange_activity_type_id()

                # If the user increased quantity of existing line or created a new line
                pickings = line.order_id.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel') and line.picking_type_id.default_location_dest_id == x.location_dest_id and x.location_dest_id.usage in ('internal', 'transit', 'customer'))
                picking = pickings and pickings[0] or False
                if not picking:
                    res = line.order_id._prepare_to_multi_picking(line.picking_type_id)
                    picking = self.env['stock.picking'].create(res)
                move_vals = line._prepare_stock_moves(picking)
                for move_val in move_vals:
                    self.env['stock.move']\
                        .create(move_val)\
                        ._action_confirm()\
                        ._action_assign()

    @api.model
    def create(self, values):
        line = super(DeliverToLine, self).create(values)
        if line.order_id.state == 'purchase':
            line._create_or_update_picking()
        return line

    def write(self, values):
        result = super(DeliverToLine, self).write(values)
        # Update expected date of corresponding moves
        if 'requsted_qty' in values:
            self.filtered(lambda l: l.order_id.state == 'purchase')._create_or_update_picking()
        return result       

    def _get_outgoing_incoming_moves(self):
        outgoing_moves = self.env['stock.move']
        incoming_moves = self.env['stock.move']

        for move in self.move_ids.filtered(lambda r: r.state != 'cancel' and not r.scrapped and self.product_id == r.product_id):
            if move.location_dest_id.usage == "supplier" and move.to_refund:
                outgoing_moves |= move
            elif move.location_dest_id.usage != "supplier":
                if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
                    incoming_moves |= move

        return outgoing_moves, incoming_moves

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    deliver_line_ids = fields.One2many('deliver.to.line', 'purchase_order_line', string='Deliver To Line',copy=False)
    deliver_to_qty = fields.Float(compute="_compute_deliver_to_qty",store=True,copy=False)

    @api.depends('deliver_line_ids.requsted_qty')
    def _compute_deliver_to_qty(self):
        for rec in self:
            rec.deliver_to_qty = sum(rec.deliver_line_ids.mapped('requsted_qty'))

    @api.constrains('deliver_to_qty')
    def _constrains_deliver_to_qty(self):
        if not self._context.get('is_copy',False):
            for rec in self:
                if rec.deliver_to_qty > rec.product_qty:
                    raise UserError(_("Total Deliver To Qty Can't Be More Than Line Qty %s") % rec.name)

    @api.model
    def create(self, values):
        line = super(PurchaseOrderLine, self).create(values)
        if line.order_id.state == 'purchase':
            if not line.order_id.multi_deliver:
                line._create_or_update_picking()
        return line
        
    def write(self, values):
        result = super(PurchaseOrderLine, self).write(values)
        if 'product_qty' in values:
            if self.order_id.multi_deliver and self.deliver_line_ids and self.product_qty <  sum(self.deliver_line_ids.mapped('requsted_qty')):
               raise UserError(_("Line Qty Can't Be Less Than Deliver To Qty %s") % sum(self.deliver_line_ids.mapped('requsted_qty')))
        return result        

    def _create_or_update_picking(self):
        for line in self:
            if not line.order_id.multi_deliver:
                if line.product_id and line.product_id.type in ('product', 'consu'):
                    # Prevent decreasing below received quantity
                    if float_compare(line.product_qty, line.qty_received, line.product_uom.rounding) < 0:
                        raise UserError(_('You cannot decrease the ordered quantity below the received quantity.\n'
                                        'Create a return first.'))

                    if float_compare(line.product_qty, line.qty_invoiced, line.product_uom.rounding) == -1:
                        # If the quantity is now below the invoiced quantity, create an activity on the vendor bill
                        # inviting the user to create a refund.
                        activity = self.env['mail.activity'].sudo().create({
                            'activity_type_id': self.env.ref('mail.mail_activity_data_warning').id,
                            'note': _('The quantities on your purchase order indicate less than billed. You should ask for a refund. '),
                            'res_id': line.invoice_lines[0].move_id.id,
                            'res_model_id': self.env.ref('account.model_account_move').id,
                        })
                        activity._onchange_activity_type_id()

                    # If the user increased quantity of existing line or created a new line
                    pickings = line.order_id.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel') and x.location_dest_id.usage in ('internal', 'transit', 'customer'))
                    picking = pickings and pickings[0] or False
                    if not picking:
                        res = line.order_id._prepare_picking()
                        picking = self.env['stock.picking'].create(res)
                    move_vals = line._prepare_stock_moves(picking)
                    for move_val in move_vals:
                        self.env['stock.move']\
                            .create(move_val)\
                            ._action_confirm()\
                            ._action_assign()

class StockMove(models.Model):
    _inherit = 'stock.move'

    deliver_to_id = fields.Many2one('deliver.to.line')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_multi_deliver = fields.Boolean(string='Multi Receipts To',default=False,default_model='purchase.order')    
