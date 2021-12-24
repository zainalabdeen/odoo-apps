from odoo import api, fields, models, tools, _

class posConfig(models.Model):
    _inherit = "pos.config"

    branch_id = fields.Many2one('company.branches')
