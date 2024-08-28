from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class TmsPurchaseOrderHeader(models.Model):
    _name = 'tms.purchase.order.header'
    _description = 'TMS Purchase Order Header'
    _rec_name = 'no'

    document_type = fields.Selection([
        ('Order', 'Order'),
        ('Return Order', 'Return Order')
    ], string='Document Type') 
    buy_from_vendor_no = fields.Char(string="Buy-From Vendor No.", size=20)
    no = fields.Char(string='No.', size=20)
    order_date = fields.Date(string="Order Date")
    posting_date = fields.Date(string="Posting Date")
    location_code = fields.Char(string="Location Code", size=10)
    vendor_shipment_no = fields.Char(string="Vendor Shipment No.", size=35)
    buy_from_vendor_name = fields.Char(string="Buy-From Vendor Name", size=50)
    buy_from_vendor_name_2 = fields.Char(string="Buy-From Vendor Name 2", size=50)
    buy_from_address  = fields.Text(string="Buy-From Address", size=50)
    buy_from_address_2 = fields.Text(string="Buy-From Address 2", size=50)
    buy_from_city = fields.Char(string="Buy-From City", size=30)
    buy_from_contact = fields.Char(string="Buy-From Contact", size=50)
    buy_from_post_code = fields.Char(string="Buy-From Post Code", size=20)
    buy_from_country = fields.Char(string="Buy-From Country", size=30)
    buy_from_country_region_code = fields.Char(string="Buy-From Country/Region Code", size=10)
    no_series = fields.Char(string="No. Series", size=10)
    posting_no_series = fields.Char(string="Posting No. Series", size=10)
    receiving_no_series = fields.Char(string="Receiving No. Series", size=10)
    status = fields.Selection([
        ('Open', 'Open'),
        ('Released', 'Released'),
        ('Pending Approval', 'Pending Approval'),
        ('Pending Prepayment', 'Pending Prepayment')
    ], string='Status')
    return_shipment_no = fields.Char(string="Return Shipment No.", size=20)
    return_shipment_no_series = fields.Char(string="Return Shipment No. Series", size=10)
    store_no = fields.Char(string="Store No.", size=10)

    purchase_order_line_ids = fields.One2many('tms.purchase.order.line', 'header_id', string='Purchase Order Lines')
    
    def create_po_receipt(self):
        receipt_headerr = self.env['tms.purchase.receipt.header'].with_context(create=True, delete=True).create({ #.with_context(create=True, delete=True)
            'source_doc_no': self.no,
            'posting_date': self.posting_date,
            'vendor_shipment_no': self.vendor_shipment_no,
        })
        return {
            'name': 'Receipt',
            'view_mode': 'form',
            'res_model': 'tms.purchase.receipt.header',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': receipt_headerr.id,
        }

class TmsPurchaseOrderLine(models.Model):
    _name = 'tms.purchase.order.line'
    _description = 'TMS Purchase Order Line'

    header_id = fields.Many2one('tms.purchase.order.header', string='Header', ondelete='cascade')
    document_type = fields.Selection([
        ('Order', 'Order'),
        ('Return Order', 'Return Order')
    ], string='Document Type')
    buy_from_vendor_no = fields.Char('Buy From Vendor No.', size=20)
    document_no = fields.Char('Document No.', size=20)
    line_no = fields.Integer('Line No.')
    type = fields.Selection([
        ('G/L Account', 'G/L Account'),
        ('Item', 'Item'),
        ('Fixed Asset', 'Fixed Asset'),
        ('Charge (Item)', 'Charge (Item)')
    ], string='Type') 
    no = fields.Char('No.', size=20)
    location_code = fields.Char('Location Code', size=10)
    description = fields.Text('Description', size=50)
    description_2 = fields.Text('Description 2', size=50)
    unit_of_measure = fields.Text('Unit Of Measure', size=10)
    quantity = fields.Float('Quantity')
    outstanding_quantity = fields.Float('Outstanding Quantity')
    qty_to_receive = fields.Float('Qty To Receive')
    qty_received = fields.Float('Qty Received')
    variant_code = fields.Char('Variant Code', size=10)
    qty_per_unit_of_measure = fields.Float('Qty. per Unit of Measure')
    unit_of_measure_code = fields.Char('Unit of Measure Code', size=10)
    quantity_base = fields.Float('Quantity (Base)')
    outstanding_qty_base = fields.Float('Outstanding Qty. (Base)')
    qty_to_invoice_base = fields.Float('Qty. to Invoice (Base)')
    qty_to_receive_base = fields.Float('Qty. to Receive (Base)')
    qty_rcd_not_invoiced_base = fields.Float('Qty. Rcd. Not Invoiced (Base)')
    qty_received_base = fields.Float('Qty. Received (Base)')
    qty_invoiced_base = fields.Float('Qty. Invoiced (Base)')
    return_qty_to_ship = fields.Float('Return Qty. to Ship')
    return_qty_to_ship_base = fields.Float('Return Qty. to Ship (Base)')
    return_qty_shipped_not_invd = fields.Float('Return Qty. Shipped Not Invd.')
    ret_qty_shpd_not_invd_base = fields.Float('Ret. Qty. Shpd Not Invd.(Base)')
    return_qty_shipped = fields.Float('Return Qty. Shipped')
    return_qty_shipped_base = fields.Float('Return Qty. Shipped (Base)')
    return_reason_code = fields.Char('Return Reason Code', size=10)
    notes = fields.Text('Notes', size=100)

