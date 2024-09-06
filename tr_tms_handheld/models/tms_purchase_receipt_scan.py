from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError    

class TMSPurchaseReceiptScanItem(models.Model):
    _name = 'tms.purchase.scan.item'
    _description = 'TMS Purchase Scan Item'
    _rec_name = 'purchase_receipt_id'
    
    purchase_receipt_id = fields.Many2one('tms.purchase.receipt.header', string='Purchase Receipt')
    item_no = fields.Many2one('tms.item', string="Item No.", domain="[('id', 'in', available_item_ids)]")
    item_description = fields.Char('Item Description', readonly=True, store=True)
    quantity =  fields.Float('Quantity')
    # sn_or_lotno = fields.Char('SN/Lot No.')
    reservation_entry_ids = fields.One2many('tms.reservation.entry', 'purchase_scan_id', string='Reservation Entry')
    item_tracking_code = fields.Char(string='Item Tracking Code', related='item_no.item_tracking_code')
    
    available_item_ids = fields.Many2many('tms.item', compute='_compute_available_item_ids', store=False)

    contains_sn = fields.Boolean(compute='_compute_contains_sn', store=True)
    contains_lot = fields.Boolean(compute='_compute_contains_lot', store=True)

    serial_number = fields.Char('Serial No.')
    lot_number = fields.Char('Lot No.')

    @api.depends('item_tracking_code')
    def _compute_contains_sn(self):
        for record in self:
            record.contains_sn = 'SN' in record.item_tracking_code if record.item_tracking_code else False
    
    @api.depends('item_tracking_code')
    def _compute_contains_lot(self):
        for record in self:
            record.contains_lot = 'LOT' in record.item_tracking_code if record.item_tracking_code else False
    
    @api.depends('purchase_receipt_id')
    def _compute_available_item_ids(self):
        """
        Domain Item. Get Item from Purchase Order
        """
        for record in self:
            if record.purchase_receipt_id:
                purchase_order = self.env['tms.purchase.order.header'].search([
                    ('no', '=', record.purchase_receipt_id.source_doc_no)
                ], limit=1)
                if purchase_order:
                    # Get IDs of available items
                    item_ids = purchase_order.purchase_order_line_ids.mapped('no.id')
                    record.available_item_ids = [(6, 0, item_ids)]
                else:
                    record.available_item_ids = [(5, 0, 0)]
            else:
                record.available_item_ids = [(5, 0, 0)]
                
    @api.onchange('item_no')
    def _onchange_item_no(self):
        """
        Auto fill Description onchange item no
        """ 
        if self.item_no and self.purchase_receipt_id:
            purchase_order = self.env['tms.purchase.order.header'].search([
                ('no', '=', self.purchase_receipt_id.source_doc_no)
            ], limit=1)
            
            if purchase_order:
                # Filter the purchase order lines
                purchase_order_line = purchase_order.purchase_order_line_ids.filtered(
                    lambda line: line.no.id == self.item_no.id
                )
                
                if purchase_order_line:
                    line = purchase_order_line[0]
                    self.item_description = line.description
                else:
                    self.item_description = False

    def clear_value(self):
        """
        Clear the value of specific fields.
        """
        self.item_no = False
        self.item_description = False
        self.quantity = False
        # self.sn_or_lotno = False
        self.reservation_entry_ids = [(5, 0, 0)]  # Clear the One2many field
    
    # V2
    def submit_purchase_receipt_line(self):
        """
        Submit Item No, Item Description, Quantity to Purchase Receipt Line
        """
        self.ensure_one()

        if not self.item_no or not self.purchase_receipt_id:
            raise UserError('Item No. must be selected.')

        if self.item_no.man_expir_date_entry_reqd and self.item_no.strict_expiration_posting:
            for entry in self.reservation_entry_ids:
                if not entry.expiration_date:
                    raise ValidationError('Expiration Date is required for item %s due to its expiration settings.' % self.item_no.no)

        purchase_order = self.env['tms.purchase.order.header'].search([
            ('no', '=', self.purchase_receipt_id.source_doc_no)
        ], limit=1)

        if not purchase_order:
            raise UserError('No matching Purchase Order found.')

        purchase_order_line = purchase_order.purchase_order_line_ids.filtered(
            lambda line: line.no.id == self.item_no.id
        )

        if not purchase_order_line:
            raise UserError('No matching Purchase Order Line found for the selected item.')

        if not self.reservation_entry_ids:
            qty_to_receive = self.quantity
        else:
            qty_to_receive = sum(entry.quantity for entry in self.reservation_entry_ids)

        # Additional data from purchase order line
        quantity = purchase_order_line[0].quantity if purchase_order_line else 0.0
        line_no = purchase_order_line[0].line_no if purchase_order_line else 0.0
        qty_received2 = purchase_order_line[0].qty_received if purchase_order_line else 0.0

        # Find or create the purchase receipt line
        receipt_line = self.env['tms.purchase.receipt.line'].search([
            ('purchase_receipt_id', '=', self.purchase_receipt_id.id),
            ('item_no', '=', self.item_no.id),
        ], limit=1)

        # Calculate the new total qty_received
        new_qty_to_received = (receipt_line.qty_to_receive if receipt_line else 0.0) + qty_to_receive

        # Validation to ensure qty_received does not exceed qty_to_receive
        if new_qty_to_received > quantity:
            raise ValidationError(
                'Total received quantity for item %s exceeds the quantity to receive.' % self.item_no.no
            )

        if receipt_line:
            receipt_line.qty_to_receive += qty_to_receive
        else:
            # Create a new receipt line
            self.env['tms.purchase.receipt.line'].create({
                'purchase_receipt_id': self.purchase_receipt_id.id,
                'item_no': self.item_no.id,
                'description': self.item_no.description,
                'quantity': quantity,
                'uom': self.item_no.base_unit_of_measure_id,
                'qty_received': qty_received2,
                'qty_to_receive': qty_to_receive,
                'line_no': line_no
            })

        # Handle serial number and lot number entries
        for entry in self.reservation_entry_ids:
            self.env['tms.reservation.entry'].create({
                'item_no': self.item_no.no,
                'source_type': '39',  # Purchase Order
                'quantity': 1 if self.contains_sn else entry.quantity,
                'serial_no': entry.serial_no,
                'expiration_date': entry.expiration_date,
                'source_id': self.purchase_receipt_id.document_no,
                'lot_no': entry.lot_no,
            })

        # Delete empty reservation records where source_id is empty
        empty_source_entries = self.env['tms.reservation.entry'].search([
            ('source_id', '=', False)
        ])
        empty_source_entries.unlink()

        self.clear_value()

    # V2

    def back_to_receipt(self):
        """
        Redirect the user back to the purchase receipt form view.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Receipt',
            'res_model': 'tms.purchase.receipt.header',
            'view_mode': 'form',
            'res_id': self.purchase_receipt_id.id,
            'target': 'inline',
        }
    
    @api.onchange('serial_number', 'lot_number')
    def _onchange_serial_or_lot(self):
        if self.serial_number or self.lot_number:
            self._create_or_update_reservation_entry()

    def _create_or_update_reservation_entry(self):
        existing_entry = self.reservation_entry_ids.filtered(
            lambda r: r.serial_no == self.serial_number or r.lot_no == self.lot_number
        )
        
        if existing_entry:
            raise UserError("The Serial Number [%s] or Lot Number [%s] already exists in the current reservation entries." % (self.serial_number, self.lot_number))
        

        reservation_domain = [
            ('source_id', '=', self.purchase_receipt_id.document_no)
        ]

        if self.serial_number:
            reservation_domain.append(('serial_no', '=', self.serial_number))
        if self.lot_number:
            reservation_domain.append(('lot_no', '=', self.lot_number))

        
        # reservation_entries = self.env['tms.reservation.entry'].search([
        #     '|',
        #     ('serial_no', '=', self.serial_number),
        #     ('lot_no', '=', self.lot_number),
        #     ('source_id', '=', self.purchase_receipt_id.document_no)
        # ])

        reservation_entries = self.env['tms.reservation.entry'].search(reservation_domain)
        if reservation_entries:
            raise UserError("The Serial Number [%s] or Lot Number [%s] already exists in the system." % (self.serial_number, self.lot_number))
        
        # Create a new entry if no duplicate is found
        self.reservation_entry_ids = [(0, 0, {
            'serial_no': self.serial_number,
            'lot_no': self.lot_number,
            'quantity': 1 if self.contains_sn else self.quantity,
            'purchase_scan_id': self.id
        })]

        self.serial_number = ''
        self.lot_number = ''
