# -*- coding: utf-8 -*-
from odoo import http

# class HrChina(http.Controller):
#     @http.route('/hr_china/hr_china/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_china/hr_china/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_china.listing', {
#             'root': '/hr_china/hr_china',
#             'objects': http.request.env['hr_china.hr_china'].search([]),
#         })

#     @http.route('/hr_china/hr_china/objects/<model("hr_china.hr_china"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_china.object', {
#             'object': obj
#         })