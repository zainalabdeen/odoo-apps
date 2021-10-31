# -*- coding: utf-8 -*-
from odoo import http

# class UserAccessRightAlternative(http.Controller):
#     @http.route('/user_access_right_alternative/user_access_right_alternative/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/user_access_right_alternative/user_access_right_alternative/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('user_access_right_alternative.listing', {
#             'root': '/user_access_right_alternative/user_access_right_alternative',
#             'objects': http.request.env['user_access_right_alternative.user_access_right_alternative'].search([]),
#         })

#     @http.route('/user_access_right_alternative/user_access_right_alternative/objects/<model("user_access_right_alternative.user_access_right_alternative"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('user_access_right_alternative.object', {
#             'object': obj
#         })