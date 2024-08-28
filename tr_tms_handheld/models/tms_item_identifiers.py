from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class TmsItemIdentifiers(models.Model):
    _name = 'tms.item.identifiers'
    _description = 'TMS Item Identifiers'
    _rec_name = 'code'

    code = fields.Char(string='Code', required=True)
    item_no = fields.Char(string='Item No.', required=True)
    variant_code = fields.Char(string='Variant Code')
    unit_of_measure_code = fields.Char(string='Unit of Measure Code')
