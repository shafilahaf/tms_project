from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class TMSCompanyInherit(models.Model):
    _inherit = 'res.company'

    ip_or_url_api = fields.Char(string='IP or URL', help='Enter the IP or URL of the NAV server')
    username_api = fields.Char(string='Username API', help='Enter the username for the API')
    password_api = fields.Char(string='Password API', help='Enter the password for the API')
    port_api = fields.Char(string='Port API', help='Enter the port for the API')