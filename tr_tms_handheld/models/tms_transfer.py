from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class TmsTransferHeader(models.Model):
    _name = 'tms.transfer.header'
    _description = 'TMS Transfer Header'
    _rec_name = 'no'

    no = fields.Char(string='No', size=20)
    transfer_from_code = fields.Char(string='Transfer-from Code', size=10)
    transfer_from_name = fields.Text(string='Transfer-from Name', size=50)
    transfer_from_name_2 = fields.Text(string='Transfer-from Name 2', size=50)
    transfer_from_address = fields.Text(string='Transfer-from Address', size=50)
    transfer_from_address_2 = fields.Text(string='Transfer-from Address 2', size=50)
    transfer_from_post_code = fields.Char(string='Transfer-from Post Code', size=20)
    transfer_from_city = fields.Text(string='Transfer-from City', size=30)
    transfer_from_county = fields.Text(string='Transfer-from County', size=30)
    transfer_from_country_region_code = fields.Char(string='Trsf.-from Country/Region Code', size=10)
    
    transfer_to_code = fields.Char(string='Transfer-to Code', size=10)
    transfer_to_name = fields.Text(string='Transfer-to Name', size=50)
    transfer_to_name_2 = fields.Text(string='Transfer-to Name 2', size=50)
    transfer_to_address = fields.Text(string='Transfer-to Address', size=50)
    transfer_to_address_2 = fields.Text(string='Transfer-to Address 2', size=50)
    transfer_to_post_code = fields.Char(string='Transfer-to Post Code', size=20)
    transfer_to_city = fields.Text(string='Transfer-to City', size=30)
    transfer_to_county = fields.Text(string='Transfer-to County', size=30)
    transfer_to_country_region_code = fields.Char(string='Trsf.-to Country/Region Code', size=10)

    posting_date = fields.Date(string='Posting Date')
    shipment_date = fields.Date(string='Shipment Date')
    receipt_date = fields.Date(string='Receipt Date')
    # status = fields.Selection([('open', 'Open'), ('released', 'Released'), ('in_transit', 'In Transit'), ('received', 'Received')], string='Status')
    status = fields.Char(string='Status', size=20)
    comment = fields.Boolean(string='Comment')
    in_transit_code = fields.Char(string='In-Transit Code', size=10)
    external_document_no = fields.Char(string='External Document No.', size=35)
    completely_shipped = fields.Boolean(string='Completely Shipped')
    completely_received = fields.Boolean(string='Completely Received')
    assigned_user_id = fields.Char(string='Assigned User ID', size=50)
    keterangan = fields.Text(string='Keterangan', size=100)
    supplier_no_packing_list = fields.Text(string='Supplier & No Packing List', size=100)
    customer_no = fields.Char(string='Customer No.', size=20)
    salesperson_code = fields.Char(string='Salesperson Code', size=20)
    location_sales_type = fields.Boolean(string='Location Sales Type')
    shipment_no_series = fields.Char(string='Shipment No Series', size=20)
    store_to = fields.Char(string='Store-to', size=10)
    # transfer_type = fields.Selection([('internal', 'Internal'), ('external', 'External')], string='Transfer Type')
    transfer_type = fields.Char(string='Transfer Type', size=20)

    transfer_line_ids = fields.One2many('tms.transfer.line', 'header_id', string='Transfer Lines')

    def create_to_shipment(self):
        trans_header = self.env['tms.handheld.transaction']
        action = trans_header.create_transaction(self.no,'Transfer','Shipment')
        return action
    
    def create_to_receipt(self):
        trans_header = self.env['tms.handheld.transaction']
        action = trans_header.create_transaction(self.no,'Transfer','Receipt')
        return action
    
    def view_to_shipment(self):
        trans_header = self.env['tms.handheld.transaction']
        action =  trans_header.view_transaction(self.no,'Transfer','Shipment')
        return action
    
    def view_to_receipt(self):
       trans_header = self.env['tms.handheld.transaction']
       action =  trans_header.view_transaction(self.no,'Transfer','Receipt')
       return action
    
class TmsTransferLine(models.Model):
    _name = 'tms.transfer.line'
    _description = 'TMS Transfer Line'
    _rec_name = 'combination'

    header_id = fields.Many2one('tms.transfer.header', string='Header')
    document_no = fields.Char(string='Document No', size=20)
    line_no = fields.Integer(string='Line No') 
    item_no = fields.Many2one('tms.item', string='No')
    no = fields.Many2one('tms.item', string='No')
    #item_no = fields.Char(string='Item No', size=20) 
    quantity = fields.Float(string='Quantity')
    uom = fields.Char(string='Unit of Measure', size=10) 
    qty_to_ship = fields.Float(string='Qty. to Ship')
    qty_to_receive = fields.Float(string='Qty. to Receive')
    qty_shipped = fields.Float(string='Quantity Shipped')
    qty_received = fields.Float(string='Quantity Received')
    status = fields.Char(string='Status', size=20)
    # status = fields.Selection([('pending', 'Pending'), ('shipped', 'Shipped'), ('received', 'Received')], string='Status')
    description = fields.Text(string='Description', size=50)
    quantity_base = fields.Float(string='Quantity (Base)')
    outstanding_qty_base = fields.Float(string='Outstanding Qty. (Base)')
    qty_to_ship_base = fields.Float(string='Qty. to Ship (Base)')
    qty_shipped_base = fields.Float(string='Qty. Shipped (Base)')
    qty_to_receive_base = fields.Float(string='Qty. to Receive (Base)')
    qty_received_base = fields.Float(string='Qty. Received (Base)')
    qty_per_uom = fields.Float(string='Qty. per Unit of Measure')
    uom_code = fields.Char(string='Unit of Measure Code', size=10)
    outstanding_quantity = fields.Float(string='Outstanding Quantity')
    variant_code = fields.Char(string='Variant Code', size=10)
    description_2 = fields.Text(string='Description 2', size=50)
    in_transit_code = fields.Char(string='In-Transit Code', size=10)
    qty_in_transit = fields.Float(string='Qty. in Transit')
    qty_in_transit_base = fields.Float(string='Qty. in Transit (Base)')
    transfer_from_code = fields.Char(string='Transfer-from Code', size=10)
    transfer_to_code = fields.Char(string='Transfer-to Code', size=10)
    shipment_date = fields.Date(string='Shipment Date')
    derived_from_line_no = fields.Integer(string='Derived From Line No.')
    keterangan_dus = fields.Text(string='Keterangan Dus', size=20)
    item_no_no = fields.Char(string='Item Number', store=True)
    combination = fields.Char(string='Combination', compute='_compute_fields_combination')

    def name_get(self):
        result = []
        for rec in self:
            display_name = f"{rec.line_no} - {rec.uom_code}"
            result.append((rec.id, display_name))
        return result
    
    @api.depends('line_no', 'uom_code')
    def _compute_fields_combination(self):
        for rec in self:
            rec.combination = str(rec.line_no) + ' - ' + rec.uom_code
