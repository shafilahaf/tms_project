# -*- coding: utf-8 -*-
# from odoo import http


# class WebStyleCustom(http.Controller):
#     @http.route('/web_style_custom/web_style_custom', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/web_style_custom/web_style_custom/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('web_style_custom.listing', {
#             'root': '/web_style_custom/web_style_custom',
#             'objects': http.request.env['web_style_custom.web_style_custom'].search([]),
#         })

#     @http.route('/web_style_custom/web_style_custom/objects/<model("web_style_custom.web_style_custom"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('web_style_custom.object', {
#             'object': obj
#         })
