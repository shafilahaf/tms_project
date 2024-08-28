from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from tkinter import *

class TmsReceiptDetailHeader(models.Model):
    _name = 'tms.receipt.detail.header'
    _description = 'TMS Receipt Detail Header'
    _rec_name = 'name'

    document_type = fields.Char(string='Document Type', required=True)
    document_date = fields.Date(string='Document Date')
    no = fields.Char(string='Receipt No.')
    related_doc_no = fields.Char(string='Related Doc No.')
    barcode = fields.Char(string='Barcode')
    name = fields.Char(string='Name', default='New', readonly=True, required=True, copy=False)

    receipt_detail_line_ids = fields.One2many('tms.receipt.detail.line', 'header_id', string='Receipt Detail Lines')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('tms.receipt.detail.header') or 'New'
        return super(TmsReceiptDetailHeader, self).create(vals)

    @api.model
    def process_barcode(self, record_id, barcode):
        """
        Process the barcode scanned by the handheld device and add the line to the receipt detail"""
        record = self.browse(record_id)
        if not record:
            raise UserError('Record not found.')

        purchase_header = self.env['tms.purchase.order.header'].search([('no', '=', record.related_doc_no)], limit=1)
        purchase_line = self.env['tms.purchase.order.line'].search([('header_id', '=', purchase_header.id), ('item_barcode', '=', barcode)], limit=1)
        if purchase_line:
            record.update({
                'receipt_detail_line_ids': [(0, 0, {
                    'line_no': purchase_line.line_no,
                    'item_no': purchase_line.item_no,
                    'uom': purchase_line.uom,
                    'item_description': purchase_line.item_description,
                    'document_type': record.document_type,
                    'document_no': record.no,
                })]
            })
        else:
            raise UserError('Barcode not found in the purchase order')
        
    def submit_receipt_detail(self):
        """
        Submit the receipt detail to the receipt header"""
        receipt_header = self.env['tms.receipt.header'].search([('no', '=', self.no)], limit=1)
        if not receipt_header:
            raise UserError('Receipt header not found.')

        for line in range(len(self.receipt_detail_line_ids)):
            receipt_line = self.env['tms.receipt.line'].create({
                'header_id': receipt_header.id,
                'line_no': line.line_no,
                'item_no': line.item_no,
                'quantity': line.quantity,
                'uom': line.uom,
                'item_description': line.item_description,
                'document_type': line.document_type,
                'document_no': line.document_no,
            })

        self.unlink()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Receipt',
            'view_mode': 'form',
            'res_model': 'tms.receipt.header',
            'res_id': receipt_header.id,
            'target': 'current',  # or 'new' to open in a new window
        }

    # @api.onchange('barcode')
    # def _onchange_barcode(self):
    #     if self.barcode:
    #         purchase_header = self.env['tms.purchase.order.header'].search([('no', '=', self.related_doc_no)], limit=1)
    #         purchase_line = self.env['tms.purchase.order.line'].search([('header_id', '=', purchase_header.id), ('item_barcode', '=', self.barcode)], limit=1)
    #         if purchase_line:
    #             self.update({
    #                 'receipt_detail_line_ids': [(0, 0, {
    #                     'line_no': purchase_line.line_no,
    #                     'item_no': purchase_line.item_no,
    #                     'uom': purchase_line.uom,
    #                     'item_description': purchase_line.item_description,
    #                 })],
    #                 'barcode': ''
    #             })
    #         else:
    #             raise UserError('Barcode not found in the purchase order')

class TmsReceiptDetailLine(models.Model):
    _name = 'tms.receipt.detail.line'
    _description = 'TMS Receipt Detail Line'

    header_id = fields.Many2one('tms.receipt.detail.header', string='Header', ondelete='cascade')
    document_type = fields.Char(string='Document Type', required=True, store=True, related='header_id.document_type')
    document_no = fields.Char(string='Document No.', required=True, store=True, related='header_id.no')
    line_no = fields.Integer(string='Line No.', required=True)
    item_no = fields.Char(string='Item No.', required=True)
    quantity = fields.Float(string='Quantity', default=1)
    uom = fields.Char(string='UOM')
    item_description = fields.Char(string='Item Description')

