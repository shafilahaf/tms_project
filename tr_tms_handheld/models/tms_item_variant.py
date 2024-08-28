from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class TmsItemVariant(models.Model):
    _name = 'tms.item.variant'
    _description = 'TMS Item Variant'
    _rec_name = 'code'

    code = fields.Char(string='Code', required=True)
    item_no = fields.Char(string='Item No.', required=True)
    description = fields.Text(string='Description')
    description_2 = fields.Text(string='Description 2')