# -*- coding: utf-8 -*-
from odoo.http import request
from odoo import http


class SwitchUser(http.Controller):

     @http.route('/web/switch_user/authenticate/', type="json",auth='user')
     def authenticate(self,db,login, password):
        request.session.__setattr__('switch_user',True)
        request.session.authenticate(db, login, password)
        return request.env['ir.http'].session_info()
