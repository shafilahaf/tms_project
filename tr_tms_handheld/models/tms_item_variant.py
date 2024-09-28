from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import requests
import logging
from requests_ntlm2 import HttpNtlmAuth

_logger = logging.getLogger(__name__)

class TmsItemVariant(models.Model):
    _name = 'tms.item.variant'
    _description = 'TMS Item Variant'
    _rec_name = 'code'

    guid = fields.Char('GUID NAV')
    code = fields.Char(string='Code', required=True)
    item_no = fields.Many2one('tms.item', string='Item', required=True)
    description = fields.Text(string='Description')
    description_2 = fields.Text(string='Description 2')
  


