from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from requests_ntlm2 import HttpNtlmAuth
import requests
import logging
import json
from datetime import date
import xml.etree.ElementTree as ET

_logger = logging.getLogger(__name__)
class TMSPurchaseReceiptHeader(models.Model):
    _name = 'tms.purchase.receipt.header'
    _description = 'TMS Purchase Receipt Header'
    _rec_name = 'document_no'
    
    document_no = fields.Char('Document No.', readonly=True)
    source_doc_no = fields.Char('Source Doc. No.', readonly=True)
    posting_date = fields.Date('Posting Date')
    vendor_shipment_no = fields.Char('Vendor Shipment No', size=35)
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    
    receipt_line_ids = fields.One2many('tms.purchase.receipt.line', 'purchase_receipt_id', string='Receipt Line')

    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Posted')], string='Status', default='draft', required=True)

    # @api.model
    # def default_get(self, fields_list):
    #     res = super(TMSPurchaseReceiptHeader, self).default_get(fields_list)
    #     if not self.env.context.get('default_id'):
    #         print("Form is being opened.")
    #     return res

    def unlink(self):
        for record in self:
            if record.state == 'submitted':
                raise UserError("You cannot delete a purchase receipt that has been Posted.")
        return super(TMSPurchaseReceiptHeader, self).unlink()
    
    @api.model
    def create(self, vals):
        if 'source_doc_no' in vals and vals['source_doc_no']:
            purchase_order = self.env['tms.purchase.order.header'].search([('no', '=', vals['source_doc_no'])], limit=1)
            if not purchase_order:
                raise ValidationError('Purchase Order not found.')

            existing_receipts = self.env['tms.purchase.receipt.header'].search([('source_doc_no', '=', vals['source_doc_no'])])
            receipt_count = len(existing_receipts) + 1
            vals['document_no'] = f"{vals['source_doc_no']}/Receipt/{receipt_count:03d}"
        else:
            raise ValidationError('Source Doc. No. is required.')

        return super(TMSPurchaseReceiptHeader, self).create(vals)
    
    def scan_itemm(self):
        self.ensure_one()
        scan_item = self.env['tms.purchase.scan.item'].create({
            'purchase_receipt_id': self.id,
        })
        return {
            'name': 'Scan Item',
            'view_mode': 'form',
            'res_model': 'tms.purchase.scan.item',
            'type': 'ir.actions.act_window',
            'target': 'inline',
            'res_id': scan_item.id,
            'context': {
                'form_view_initial_mode': 'edit',
                'create': False, 'edit': True, 'delete': True
            }
        }
        
    def submit(self):
        """
        This method will change the status of the receipt to 'Submitted' and change quantity in line to purchase order nav
        """
        url = f'http://{self.company.ip_or_url_api}:{self.company.port_api}/Thomasong/OData/Company(\'{self.company.name}\')/Handheld_Line_OData?$format=json'
        headers = {'Content-Type': 'application/json'}

        username = self.company.username_api
        password = self.company.password_api
        
        auth = HttpNtlmAuth(username, password)  # Using requests_ntlm2

        for line in self.receipt_line_ids:
            check_sn_info = False
            if line.item_no.sn_specific_tracking == True:
                check_sn_info = True
            elif line.item_no.sn_purchase_inbound_tracking == True:
                check_sn_info = True
            elif line.item_no.lot_specific_tracking == True:
                check_sn_info = True
            elif line.item_no.lot_purchase_inbound_tracking == True:
                check_sn_info = True
            data = {
                "Document_Type": "Purchase Order",
                "Document_No": self.source_doc_no,
                "Line_No": str(line.line_no),
                "Quantity": str(line.qty_to_receive),
                "Processed_Header_ID": str(self.id),
                "Item_No": line.item_no.no,
                "External_Document_No" : str(self.vendor_shipment_no),
            }
            
            response = requests.post(url, headers=headers, auth=auth, json=data)
            
            if response.status_code == 400 :
                response_json = response.json()
                resp = response_json.get('odata.error', {}).get('message', {}).get('value', f'Nav Error {response.text}' )
                raise ValidationError(resp)
            
            if line.item_no and (check_sn_info==True):
                self.handheld_sn()

        #posting - send to transaction nav
        self.posting_receipt()

        purchase_order = self.env['tms.purchase.order.header'].search([('no', '=', self.source_doc_no)], limit=1)
        if not purchase_order:
            raise ValidationError('Related Purchase Order not found.')
        
        self.state = 'submitted'
        
        return {
            'name': 'Purchase Order',
            'view_mode': 'form',
            'res_model': 'tms.purchase.order.header',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': purchase_order.id,
            'context': {
                'create': False, 'edit': False, 'delete': False
            }
        }
    
    def handheld_sn(self):
        """
        Handheld SN ODATA
        """
        # url = f'http://{self.company.ip_or_url_api}:{self.company.port_api}/Thomasong/OData/Company(\'{self.company.name}\')/Handheld_SN_OData?$format=json'
        url = f"http://192.168.1.5:9148/Thomasong/OData/Company('THOMASONG')/Handheld_SN_OData?$format=json"
        headers = {'Content-Type': 'application/json'}

        username = self.company.username_api
        password = self.company.password_api
        
        auth = HttpNtlmAuth(username, password)  # Using requests_ntlm2

        reservation_entries = self.env['tms.reservation.entry'].search([
            ('source_id','=',self.document_no)
        ])
        
        if reservation_entries:
            for entry in reservation_entries:
                receipt_line = self.env['tms.purchase.receipt.line'].search([
                    ('item_no.no', '=', entry.item_no),
                    ('purchase_receipt_id', '=', self.id)
                ], limit=1)
                
                # if not receipt_line:
                #     _logger.warning(f"No matching receipt line found for item {entry.item_no.id} in receipt {self.id}")
                #     continue
                
                data_sn = {
                    "Processed_Header_ID": str(self.id),
                    "Line_ID": str(receipt_line.id),
                    "Line_No": str(receipt_line.line_no),
                    "Serial_No": entry.serial_no if entry.serial_no else "",
                    "Lot_No": entry.lot_no if entry.lot_no else "",
                    "Expired_Date": entry.expiration_date.isoformat() if entry.expiration_date else date.min.isoformat(),
                    "Quantity": str(entry.quantity)
                }
                
                response = requests.post(url, headers=headers, auth=auth, json=data_sn)
                
                if response.status_code == 400 :
                    response_json = response.json()
                    resp = response_json.get('odata.error', {}).get('message', {}).get('value', f'Nav Error {response.text}' )
                    raise ValidationError(resp)
              
        else:
            raise UserError('No SN/LOT Detail')
        
    def posting_receipt(self):
        """
        Posting Receipt to NAV
        """
        url2 = f'http://{self.company.ip_or_url_api}:{self.company.port_api}/Thomasong/OData/Company(\'{self.company.name}\')/Handheld_Action_Odata?$format=json'
        headers = {'Content-Type': 'application/json'}

        username = self.company.username_api
        password = self.company.password_api
        
        auth = HttpNtlmAuth(username, password)  # Using requests_ntlm2

        if self.posting_date == False:
            raise UserError('Please enter the Posting Date before submit')

        data2 = {
             'Document_Type': "Purchase Order",
             'Document_No': self.source_doc_no,
             "Processed_Header_ID": str(self.id),
             "Posting_Date": self.posting_date.isoformat(),
             'Post_Action': str(1),
             
        }

        response = requests.post(url2, headers=headers, auth=auth, json=data2)

        if response.status_code == 400 :
            response_json = response.json()
            resp = response_json.get('odata.error', {}).get('message', {}).get('value',  f'Nav Error {response.text}' )
            raise ValidationError(resp)
        elif response.status_code == 201 :
           self.fnCreateMessage(f'Purchase Receive No. {self.document_no} succesfully Posted')
                                 

    def fnCreateMessage(self,message) :
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Calculate Salary',
                'message': message,
                'sticky': False}
        }        

   
    
class TMSPurchaseReceiptLine(models.Model):
    _name = 'tms.purchase.receipt.line'
    _description = 'TMS Purchase Receipt line'
    
    purchase_receipt_id = fields.Many2one('tms.purchase.receipt.header', string='Purchase Receipt')
    # item_no = fields.Char('Item No.', readonly=True)
    line_no = fields.Integer('Line No.', store=True)
    item_no = fields.Many2one('tms.item', string="Item No.", domain="[('id', 'in', available_item_ids)]")
    description = fields.Char('Description', readonly=True, store=True)
    quantity = fields.Float('Quantity', readonly=True, store=True)
    uom = fields.Char(string="Unit of Measure", readonly=True, store=True)
    qty_to_receive = fields.Float('Qty To Receive',readonly=True, store=True)
    qty_received = fields.Float('Qty Received')
    item_tracking_code = fields.Char(string='Item Tracking Code', related='item_no.item_tracking_code',store=True)
    
    available_item_ids = fields.Many2many('tms.item', compute='_compute_available_item_ids', store=False)


    
    @api.depends('purchase_receipt_id')
    def _compute_available_item_ids(self):
        """
        Domain Item. Get Item from Purchase Order"""
        for line in self:
            if line.purchase_receipt_id:
                purchase_order = self.env['tms.purchase.order.header'].search([
                    ('no', '=', line.purchase_receipt_id.source_doc_no)
                ], limit=1)
                if purchase_order:
                    line.available_item_ids = purchase_order.purchase_order_line_ids.mapped('no.id')
                else:
                    line.available_item_ids = False
            else:
                line.available_item_ids = False
                
    @api.onchange('item_no')
    def _onchange_item_no(self):
        """
        Auto fill Description, Quantity, UoM onchange item no
        """
        if self.item_no and self.purchase_receipt_id:
            purchase_order = self.env['tms.purchase.order.header'].search([
                ('no', '=', self.purchase_receipt_id.source_doc_no)
            ], limit=1)
            
            if purchase_order:
                # Filter the purchase order lines based on the selected item_no
                purchase_order_line = purchase_order.purchase_order_line_ids.filtered(
                    lambda line: line.no == self.item_no.no
                )
                
                if purchase_order_line:
                    # If multiple lines are found, limit to the first one
                    line = purchase_order_line[0]
                    self.description = line.description
                    self.quantity = line.quantity
                    self.uom = line.unit_of_measure_code
                    self.qty_to_receive = line.qty_to_receive
                    self.line_no = line.line_no
                else:
                    self.description = False
                    self.quantity = 0.0
                    self.uom = False
                    self.qty_to_receive = 0.0
                    
    def action_view_reservation_entries(self):
        #Details
        self.ensure_one()
        action = self.env.ref('tr_tms_handheld.action_tms_reservation_entry').read()[0]
        
        action['domain'] = [('item_no', '=', self.item_no.no),
                            ('source_id', '=', self.purchase_receipt_id.document_no)]
        
        action['context'] = dict(self.env.context, create=False, edit=False)
        
        return action
    
    def unlink(self):
        for line in self:
            # Search for the corresponding reservation entries
            reservation_entries = self.env['tms.reservation.entry'].search([
                ('item_no', '=', line.item_no.no),
                ('source_id', '=', line.purchase_receipt_id.document_no)
            ])
            # Delete the found reservation entries
            reservation_entries.unlink()
        
        # Call the super method to delete the purchase receipt line
        return super(TMSPurchaseReceiptLine, self).unlink()

