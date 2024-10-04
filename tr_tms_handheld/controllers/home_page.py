from odoo import http
from odoo.http import request

class MyModuleHomeController(http.Controller):
    @http.route('/tms/home_page', auth='public', website=True)
    def home(self, **kwargs):
        return request.render('tr_tms_handheld.my_module_home_page')