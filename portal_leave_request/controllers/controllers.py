# -*- coding: utf-8 -*-
from odoo import http

# class PortalLeaveRequest(http.Controller):
#     @http.route('/portal_leave_request/portal_leave_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/portal_leave_request/portal_leave_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('portal_leave_request.listing', {
#             'root': '/portal_leave_request/portal_leave_request',
#             'objects': http.request.env['portal_leave_request.portal_leave_request'].search([]),
#         })

#     @http.route('/portal_leave_request/portal_leave_request/objects/<model("portal_leave_request.portal_leave_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('portal_leave_request.object', {
#             'object': obj
#         })