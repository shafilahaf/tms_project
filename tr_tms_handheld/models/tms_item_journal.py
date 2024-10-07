from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

class TMSItemJournalHeader(models.Model):
    _name = 'tms.item.journal'
    _description = 'TMS Item Journal'
    _rec_name = 'no'

    no = fields.Char('No.')
    document_type = fields.Selection([
        ('Phys. Inv. Journal', 'Phys. Inv. Journal'),
        ('Item Journal', 'Item Journal')
    ], string='Document Type')
    posting_date = fields.Date('Posting Date')
    location_code = fields.Many2one('tms.locations', string='Location Code')
    journal_template_name = fields.Char('Journal Template Name')
    journal_batch_name = fields.Char('Journal Batch Name')
    status = fields.Char('Status')
    item_journal_line_ids = fields.One2many('tms.item.journal.line', 'header_id', string='Item Journal Line')

    def create_transaction_header(self):
        trans_header = self.env['tms.handheld.transaction']
        action = trans_header.create_transaction(self.no,'Item Journal',self.document_type)
        return action
    
    def view_transaction_header(self):
        trans_header = self.env['tms.handheld.transaction']
        action =  trans_header.view_transaction(self.no,'Item Journal',self.document_type)
        return action


class TMSItemJournalLine(models.Model):
    _name = 'tms.item.journal.line'
    _description = 'TMS Item Journal Line'
    _rec_name = 'document_no'
    
    header_id = fields.Many2one('tms.item.journal', string='Header')
    document_no = fields.Char('Document No')
    line_no = fields.Integer('Line No')
    posting_date = fields.Date('Posting Date')
    entry_type = fields.Selection([
        ('Positive Adjusment', 'Positive Adjusment'),
        ('Negative Adjusment', 'Negative Adjusment'),
    ], string='Entry Type')
    item_no_code = fields.Many2one('tms.item', string='Item No. Code')
    description = fields.Char('Description')
    unit_of_measure_code = fields.Many2one('tms.unit.of.measures', string='Unit of Measure Code')
    quantity = fields.Float('Quantity')
