from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class TmsItemIdentifiers(models.Model):
    _name = 'tms.item.identifiers'
    _description = 'TMS Item Identifiers'
    _rec_name = 'code'

    code = fields.Char(string='Code')
    item_no = fields.Many2one('tms.item', string='Item')
    variant_code = fields.Char(string='Variant Code')
    unit_of_measure_code = fields.Many2one('tms.unit.of.measures', string='Unit of Measures')
    
    
