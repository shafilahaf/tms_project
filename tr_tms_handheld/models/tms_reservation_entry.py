from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

class TMSReservationEntry(models.Model):
    _name = 'tms.reservation.entry'
    _description = 'TMS Reservation Entry'
    
    item_no = fields.Char('Item No')
    location_code = fields.Char('Location Code')
    source_type = fields.Selection([
        ('39', 'Purchase Order'),
        ('37', 'Sales Order'),
        ('5741', 'Transfer Order'),
        ('83', 'Item Journal')
    ], string="Source Type")
    source_id = fields.Char('Source Id') # Doc No.
    source_ref_no = fields.Integer('Source Ref.') # Line No.
    quantity = fields.Float('Quantity')
    expiration_date = fields.Date('Expiration Date')
    serial_no = fields.Char('Serial No.')
    lot_no = fields.Char('Lot No.')
    source_type_int = fields.Integer('Source Type Int', compute='_compute_source_type_int', store=True)
    
    purchase_scan_id = fields.Many2one('tms.purchase.scan.item', string='purchase_scan_id')
    
    ##
    line_id = fields.Integer('Line_ID')
    line_no = fields.Integer('Line No')
    
    @api.depends('source_type')
    def _compute_source_type_int(self):
        for record in self:
            # Map selection values to integer values
            source_type_map = {
                '39': 39,   # Purchase Order
                '37': 37,   # Sales Order
                '5741': 5741, # Transfer Order
                '83': 83    # Item Journal
            }
            record.source_type_int = source_type_map.get(record.source_type, 0)