from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import requests
import logging
# from requests_ntlm2 import HttpNtlmAuth

_logger = logging.getLogger(__name__)

class TMSSalesWizard(models.Model):
  _name = 'tms.sales.wizard'
  _description = 'TMS Sales Wizard'

  description = fields.Char(string='Description', required=True, default='This is wizard for syncing sales order from NAV to Odoo')
  company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
  
  # def get_sales_header(self):
    
    
  # def get_sales_line(self):
    