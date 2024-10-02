from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class TmsLocations(models.Model):
    _name = 'tms.locations'
    _description = 'TMS Location'
    _rec_name = 'code'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')