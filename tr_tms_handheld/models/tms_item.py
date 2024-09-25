from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class TmsItem(models.Model):
    _name = 'tms.item'
    _description = 'TMS Item'
    _rec_name = 'combination'

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
    man_expir_date_entry_reqd = fields.Boolean('Man. Expir. Date Entry Reqd.', default=False)
    strict_expiration_posting = fields.Boolean('Strict Expiration Posting', default=False)
    sn_specific_tracking = fields.Boolean('SN Specific Tracking', default=False)
    sn_purchase_inbound_tracking = fields.Boolean('SN Purchase Inbound Tracking', default=False)
    sn_purchase_outbound_tracking = fields.Boolean('SN Purchase Outbound Tracking', default=False)
    sn_sales_inbound_tracking = fields.Boolean('SN Sales Inbound Tracking', default=False)
    sn_sales_outbound_tracking = fields.Boolean('SN Sales Outbound Tracking', default=False)
    sn_pos_adjmt_inb_tracking = fields.Boolean('SN Pos. Adjmt. Inb. Tracking', default=False)
    sn_pos_adjmt_outb_tracking =fields.Boolean('SN Pos. Adjmt. Outb. Tracking', default=False)
    sn_neg_adjmt_inb_tracking = fields.Boolean('SN Neg. Adjmt. Inb. Tracking', default=False)
    sn_neg_adjmt_outb_tracking = fields.Boolean('SN Neg. Adjmt. Outb. Tracking', default=False)
    sn_transfer_tracking = fields.Boolean('SN Transfer Tracking', default=False)
    lot_specific_tracking = fields.Boolean('Lot Specific Tracking', default=False)
    lot_purchase_inbound_tracking = fields.Boolean('Lot Purchase Inbound Tracking', default=False)
    lot_purchase_outbound_tracking=fields.Boolean('Lot Purchase Outbound Tracking', default=False)
    lot_sales_inbound_tracking = fields.Boolean('Lot Sales Inbound Tracking', default=False)
    lot_sales_outbound_tracking = fields.Boolean('Lot Sales Outbound Tracking', default=False)
    lot_pos_adjmt_inb_tracking =fields.Boolean('Lot Pos. Adjmt. Inb. Tracking', default=False)
    lot_pos_adjmt_outb_tracking =fields.Boolean('Lot Pos. Adjmt. Outb. Tracking', default=False)
    lot_neg_adjmt_inb_tracking = fields.Boolean('Lot Neg. Adjmt. Inb. Tracking', default=False)
    lot_neg_adjmt_outb_tracking=fields.Boolean('Lot Neg. Adjmt. Outb. Tracking', default=False)
    lot_transfer_tracking = fields.Boolean('Lot Transfer Tracking', default=False)
    barcode = fields.Char(string="Barcode")
    
    has_been_sent_to_nav = fields.Boolean(string='Has been sent to NAV', default=False)
    etag = fields.Char(string='ETag')
    
    combination = fields.Char(string='Combination', compute='_compute_fields_combination')

    def open_item_identifiers(self):
        default_uom_code = self.env['tms.unit.of.measures'].search([
            ('code','=', self.base_unit_of_measure_id)
        ], limit=1)
        return {
            'name': 'Item Identifiers',
            'type': 'ir.actions.act_window',
            'res_model': 'tms.item.identifiers',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': {
                'default_item_no': self.id,
                # 'default_unit_of_measure_code': default_uom_code.id,
                'create': True, 'edit': True, 'delete': True,
                'from_odoo': True,
            },
            'domain': [('item_no', '=', self.id)]
        }


    
    @api.depends('no', 'description')
    def _compute_fields_combination(self):
        for test in self:
            test.combination = test.no + ' - ' + test.description
    
    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
    #     args = list(args or [])
    #     domain = []
    #     if name:
    #         # Build the domain to search by 'no' or 'description'
    #         domain = ['|', '|', ('no', operator, name), ('description', operator, name)]
    #     # Perform the search with the domain
    #     recordset = self.search(domain + args, limit=limit)
    #     return recordset.name_get()
    
    def name_get(self):
        result = []
        for rec in self:
            display_name = f"{rec.no} - {rec.description}"
            result.append((rec.id, display_name))
        return result