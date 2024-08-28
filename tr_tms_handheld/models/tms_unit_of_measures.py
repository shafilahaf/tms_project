from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class TmsUnitOfMeasures(models.Model):
    _name = 'tms.unit.of.measures'
    _description = 'TMS Unit of Measures'
    _rec_name = 'code'

    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description', required=True)
    
