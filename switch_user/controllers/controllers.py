# -*- coding: utf-8 -*-
from odoo.http import request
from odoo import http

#DEFAULT_CRYPT_CONTEXT

class SwitchUser(http.Controller):
     @http.route('/switch_user/switch_user/', type="json",auth='public')
     def index(self, **kw):
        print(">>>>>>>>>>>>>>>>>>>>>>",kw)
        request.env.cr.execute(
            "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
            [kw['user']]
        )
        [hashed] = request.env.cr.fetchone()
        databse = request.session.db


        return {'db':databse,'user':kw['user'],'password':hashed}

#     @http.route('/switch_user/switch_user/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('switch_user.listing', {
#             'root': '/switch_user/switch_user',
#             'objects': http.request.env['switch_user.switch_user'].search([]),
#         })

#     @http.route('/switch_user/switch_user/objects/<model("switch_user.switch_user"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('switch_user.object', {
#             'object': obj
#         })