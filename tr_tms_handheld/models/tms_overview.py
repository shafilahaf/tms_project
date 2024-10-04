from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class TMSOverview(models.Model):
    _name = 'tms.overview'