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
    
    def unlink(self):
        """
        Override the unlink method to update qty_to_receive in tms.purchase.receipt.line 
        when a reservation entry is deleted.
        """
        for entry in self:

            purchase_receipt_header = self.env['tms.purchase.receipt.header'].search([
                ('document_no', '=', entry.source_id)
            ], limit=1)

            # Prevent delete when purchase receipt submit
            if purchase_receipt_header and purchase_receipt_header.state in ['submitted']:
                raise ValidationError("You cannot delete a reservation entry when the related purchase receipt is posted or submitted.")
            

            purchase_receipt_line = self.env['tms.purchase.receipt.line'].search([
                ('item_no.no', '=', entry.item_no),
                ('purchase_receipt_id.document_no', '=', entry.source_id)
            ], limit=1)

            if purchase_receipt_line:
                remaining_reservation_entries = self.env['tms.reservation.entry'].search([
                    ('item_no', '=', entry.item_no),
                    ('source_id', '=', entry.source_id),
                    ('id', '!=', entry.id)  
                ])

                if remaining_reservation_entries:
                    purchase_receipt_line.qty_to_receive = sum(remaining_reservation_entries.mapped('quantity'))
                    abcd = sum(remaining_reservation_entries.mapped('quantity'))
                    print(abcd)
                else:
                    purchase_receipt_line.qty_to_receive = 0.0

        return super(TMSReservationEntry, self).unlink()