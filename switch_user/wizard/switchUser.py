# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class switchUser(models.TransientModel):
    _name = 'switch.user'
    _description = 'Enable User Switching'

    user_id = fields.Many2one('res.users')