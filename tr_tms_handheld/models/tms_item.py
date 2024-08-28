from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class TmsItem(models.Model):
    _name = 'tms.item'
    _description = 'TMS Item'
    _rec_name = 'no'

    no = fields.Char(string='No.', required=True)
    description = fields.Text(string='Description', required=True)
    search_description = fields.Char(string='Search Description')
    description_2 = fields.Text(string='Description 2')
    base_unit_of_measure_id = fields.Char(string="Base Unit of Measure")
    inventory_posting_group = fields.Char(string='Inventory Posting Group')
    vendor_no = fields.Char(string='Vendor No.')
    vendor_item_no = fields.Text(string='Vendor Item No.')
    manufacturer_code = fields.Char(string='Manufacturer Code')
    item_category_code = fields.Char(string='Item Category Code')
    product_group_code = fields.Char(string='Product Group Code')
    item_tracking_code = fields.Char(string='Item Tracking Code')
    division_code = fields.Char(string='Division Code')
    man_expir_date_entry_reqd = fields.Boolean('Man. Expir. Date Entry Reqd.')
    strict_expiration_posting = fields.Boolean('Strict Expiration Posting')
    sn_specific_tracking = fields.Boolean('SN Specific Tracking')
    sn_purchase_inbound_tracking = fields.Boolean('SN Purchase Inbound Tracking')
    sn_purchase_outbound_tracking = fields.Boolean('SN Purchase Outbound Tracking')
    sn_sales_inbound_tracking = fields.Boolean('SN Sales Inbound Tracking')
    sn_sales_outbound_tracking = fields.Boolean('SN Sales Outbound Tracking')
    sn_pos_adjmt_inb_tracking = fields.Boolean('SN Pos. Adjmt. Inb. Tracking')
    sn_pos_adjmt_outb_tracking =fields.Boolean('SN Pos. Adjmt. Outb. Tracking')
    sn_neg_adjmt_inb_tracking = fields.Boolean('SN Neg. Adjmt. Inb. Tracking')
    sn_neg_adjmt_outb_tracking = fields.Boolean('SN Neg. Adjmt. Outb. Tracking')
    sn_transfer_tracking = fields.Boolean('SN Transfer Tracking')
    lot_specific_tracking = fields.Boolean('Lot Specific Tracking')
    lot_purchase_inbound_tracking = fields.Boolean('Lot Purchase Inbound Tracking')
    lot_purchase_outbound_tracking=fields.Boolean('Lot Purchase Outbound Tracking')
    lot_sales_inbound_tracking = fields.Boolean('Lot Sales Inbound Tracking')
    lot_sales_outbound_tracking = fields.Boolean('Lot Sales Outbound Tracking')
    lot_pos_adjmt_inb_tracking =fields.Boolean('Lot Pos. Adjmt. Inb. Tracking')
    lot_pos_adjmt_outb_tracking =fields.Boolean('Lot Pos. Adjmt. Outb. Tracking')
    lot_neg_adjmt_inb_tracking = fields.Boolean('Lot Neg. Adjmt. Inb. Tracking')
    lot_neg_adjmt_outb_tracking=fields.Boolean('Lot Neg. Adjmt. Outb. Tracking')
    lot_transfer_tracking = fields.Boolean('Lot Transfer Tracking')
    
    has_been_sent_to_nav = fields.Boolean(string='Has been sent to NAV', default=False)
    etag = fields.Char(string='ETag')