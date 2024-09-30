from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class TmsSalesHeader(models.Model):
    _name = "tms.sales.order.header"
    _description = "TMS Sales Header"
    _rec_no = 'no'

    document_type = fields.Selection([
        ('Order', 'Order'),
        ('Return Order', 'Return Order')
    ], string="Document Type")
    sell_to_customer_no = fields.Char(string="Sell-to Customer No.",  size=20)
    no = fields.Char(string="No",  size=20)
    order_date = fields.Date(string="Order Date")
    posting_date = fields.Date(string="Posting Date")
    shipment_date = fields.Date(string="Shipment Date")
    location_code = fields.Char(string="Location Code", size=10)
    sell_to_customer_name = fields.Text(string="Sell-to Customer Name",  size=50)
    sell_to_customer_name_2 = fields.Text(string="Sell-to Customer Name 2", size=50)
    sell_to_address = fields.Text(string="Sell-to Address", size=50)
    sell_to_address_2 = fields.Text(string="Sell-to Address 2", size=50)
    sell_to_city = fields.Text(string="Sell-to City", size=30)
    sell_to_contact = fields.Text(string="Sell-to Contact", size=50)
    sell_to_post_code = fields.Char(string="Sell-to Post Code", size=20)
    sell_to_county = fields.Text(string="Sell-to County", size=30)
    sell_to_country_region_code = fields.Char(string="Sell-to Country/Region Code", size=10)
    ship_to_post_code = fields.Char(string="Ship-to Post Code", size=20)
    ship_to_county = fields.Text(string="Ship-to County", size=30)
    ship_to_country_region_code = fields.Char(string="Ship-to Country/Region Code", size=10)
    shipping_agent_code = fields.Char(string="Shipping Agent Code", size=10)
    package_tracking_no = fields.Text(string="Package Tracking No.", size=30)
    posting_no_series = fields.Char(string="Posting No. Series", size=10)
    shipping_no_series = fields.Char(string="Shipping No. Series", size=10)
    status = fields.Selection([
        ('Open', 'Open'),
        ('Released', 'Released'),
        ('Pending Approval', 'Pending Approval'),
        ('Pending Prepayment', 'Pending Prepayment')
    ], string="Status")
    return_receipt_no_series = fields.Char(string="Return Receipt No. Series", size=10)
    store_no = fields.Char(string="Store No.", size=10)
    complete_shipment = fields.Boolean('Complete Shipment')
    

    sales_line_ids = fields.One2many(
        "tms.sales.order.line", "header_id", string="Sales Lines"
    )

    def create_transaction_header(self):
        trans_header = self.env['tms.handheld.transaction']
        action = trans_header.create_transaction(self.no,'Sales',self.document_type)
        return action
    
    def view_transaction_header(self):
        trans_header = self.env['tms.handheld.transaction']
        action =  trans_header.view_transaction(self.no,'Sales',self.document_type)
        return action

class TmsSalesLine(models.Model):
    _name = "tms.sales.order.line"
    _description = "TMS Sales Line"

    header_id = fields.Many2one("tms.sales.order.header", string="Header")
    document_type = fields.Selection([
        ('Quote', 'Quote'),
        ('Order', 'Order'),
        ('Invoice', 'Invoice'),
        ('Credit Memo', 'Credit Memo'),
        ('Blanket Order', 'Blanket Order'),
        ('Return Order', 'Return Order')
    ], string="Document Type")
    sell_to_customer_no = fields.Char(string="Sell-to Customer No.",  size=20)
    document_no = fields.Char(string="Document No",  store=True, size=20)
    line_no = fields.Integer(string="Line No")
    type = fields.Selection([
        ('G/L Account', 'G/L Account'),
        ('Item', 'Item'),
        ('Resource', 'Resource'),
        ('Fixed Asset', 'Fixed Asset'),
        ('Charge (Item)', 'Charge (Item)')
    ], string="Type")
    no = fields.Char(string="No.",  size=20)
    location_code = fields.Char(string="Location Code", size=10)
    description = fields.Text(string="Description", size=50)
    description_2 = fields.Text(string="Description 2", size=50)
    unit_of_measure = fields.Text(string="Unit of Measure", size=10)
    quantity = fields.Float(string="Quantity")
    outstanding_quantity = fields.Float(string="Outstanding Quantity")
    qty_to_ship = fields.Float(string="Qty. to Ship")
    quantity_shipped = fields.Float(string="Quantity Shipped")
    variant_code = fields.Char(string="Variant Code", size=10)
    qty_per_unit_of_measure = fields.Float(string="Qty. per Unit of Measure")
    unit_of_measure_code = fields.Char(string="Unit of Measure Code", size=10)
    quantity_base = fields.Float(string="Quantity (Base)")
    outstanding_qty_base = fields.Float(string="Outstanding Qty. (Base)")
    qty_to_invoice_base = fields.Float(string="Qty. to Invoice (Base)")
    qty_to_ship_base = fields.Float(string="Qty. to Ship (Base)")
    qty_shipped_not_invd_base = fields.Float(string="Qty. Shipped Not Invd. (Base)")
    qty_shipped_base = fields.Float(string="Qty. Shipped (Base)")
    qty_invoiced_base = fields.Float(string="Qty. Invoiced (Base)")
    return_qty_to_receive = fields.Float(string="Return Qty. to Receive")
    return_qty_to_receive_base = fields.Float(string="Return Qty. to Receive (Base)")
    return_qty_rcd_not_invd = fields.Float(string="Return Qty. Rcd. Not Invd.")
    return_qty_rcd_not_invd_base = fields.Float(string="Ret. Qty. Rcd. Not Invd.(Base)")
    return_qty_received = fields.Float(string="Return Qty. Received")
    return_qty_received_base = fields.Float(string="Return Qty. Received (Base)")
    return_reason_code = fields.Char(string="Return Reason Code", size=10)
