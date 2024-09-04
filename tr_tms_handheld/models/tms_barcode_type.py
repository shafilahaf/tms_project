from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class TMsBarcodeType(models.Model):
    _name = 'tms.barcode.type'
    _description = 'TMS Barcode Type'
    
    name = fields.Char('Name')