# -*- coding: utf-8 -*-
from odoo import http

# class EbsProcess(http.Controller):
#     @http.route('/ebs_process/ebs_process/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ebs_process/ebs_process/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ebs_process.listing', {
#             'root': '/ebs_process/ebs_process',
#             'objects': http.request.env['ebs_process.ebs_process'].search([]),
#         })

#     @http.route('/ebs_process/ebs_process/objects/<model("ebs_process.ebs_process"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ebs_process.object', {
#             'object': obj
#         })