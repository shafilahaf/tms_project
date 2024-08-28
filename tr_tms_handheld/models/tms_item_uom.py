from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class TmsItemUom(models.Model):
    _name = 'tms.item.uom'
    _description = 'TMS Item UOM'
    _rec_name = 'code'

    item_no = fields.Char(string='Item No.')
    code = fields.Char(string='Code', required=True)
    qty_per_unit_of_measure = fields.Float(string='Qty per UoM')
