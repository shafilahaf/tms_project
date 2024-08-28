from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

class TMSItemJournalLine(models.Model):
    _name = 'tms.item.journal.line'
    _description = 'TMS Item Journal Line'
    _rec_name = 'item_no'

    line_no = fields.Integer('Line No.')
    item_no = fields.Char('Item No', size=20)
    posting_date = fields.Date('Posting Date')
    entry_type = fields.Selection([
        ('Purchase', 'Purchase'),
        ('Sale', 'Sale'),
        ('Positive Adjmt.', 'Positive Adjmt.'),
        ('Negative Adjmt.', 'Negative Adjmt.'),
        ('Transfer', 'Transfer'),
        ('Consumption', 'Consumption'),
        ('Output', 'Output'),
        ('Assembly Consumption', 'Assembly Consumption'),
        ('Assembly Output', 'Assembly Output'),
    ], string='Entry Type')
    document_no = fields.Char('Document No', size=20)
    description = fields.Char('Description', size=50)
    location_code = fields.Char('Location Code', size=10)
    quantity = fields.Float('Quantity')
    journal_batch_name = fields.Char('Journal Batch Name', size=10)
    qty_calculated = fields.Float('Qty. (Calculated)')
    qty_phys_inventory = fields.Float('Qty. (Phys. Inventory)')
    phys_inventory = fields.Boolean('Phys. Inventory')
    external_document_no = fields.Char('External Document No.', size=35)
    variant_code = fields.Char('Variant Code', size=10)
    qty_per_unit_measure = fields.Float('Qty. per Unit of Measure')
    unit_of_measure_code = fields.Char('Unit of Measure Code', size=10)
    quantity_base = fields.Float('Quantity (Base)')