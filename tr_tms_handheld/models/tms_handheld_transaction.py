from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
from requests_ntlm2 import HttpNtlmAuth
import requests
import logging
import json
from datetime import date
import xml.etree.ElementTree as ET

_logger = logging.getLogger(__name__)
class TMSHandheldReceipt(models.Model):
    _name = 'tms.handheld.transaction' # tms.handheld.transaction
    _description = 'TMS Handheld Transaction'
    _rec_name = 'document_no'
    
    document_type = fields.Selection([('1', 'Purchase Receipt Order'), ('2', 'Purchase Return Shipment'),('3', 'Sales Shipment Order'), ('4', 'Sales Return Receipt')], string='Document Type')
    document_no = fields.Char('Document No.', readonly=True)
    source_doc_no = fields.Char('Source Doc. No.', readonly=True)
    posting_date = fields.Date('Posting Date')
    vendor_shipment_no = fields.Char('Vendor Shipment No', size=35)
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    transaction_line_ids = fields.One2many('tms.handheld.transaction.line', 'handheld_transaction_id', string='Receipt Line')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Posted')], string='Status', default='draft', required=True)
    noseries_count = fields.Integer(string = 'No Series Count')

    def back_to_transaction(self):
        if self.document_type in ['1', '2']:
            trans = self.env['tms.purchase.order.header'].search([('no', '=', self.source_doc_no)], limit=1)
            title = "Purchase"
            model = 'tms.purchase.order.header'
            ref_view = 'tms_purchase_order_header_view_form'
            if not trans:
                raise UserError(_('No Purchase Order found with the Source Doc No: %s') % self.source_doc_no)
        elif self.document_type in ['3','4']:
            trans = self.env['tms.sales.order.header'].search([('no', '=', self.source_doc_no)], limit=1)
            title = "Sales"
            model = 'tms.sales.order.header'
            ref_view = 'tms_sales_header_view_form'
            if not trans:
                raise UserError(_('No Sales Order found with the Source Doc No: %s') % self.source_doc_no)
        
        page = {
            'name': f"{title}",
            'view_mode': 'form',
            'res_model': f"{model}",
            'type': 'ir.actions.act_window',
            'res_id': trans.id,
            'views': [(self.env.ref(f'tr_tms_handheld.{ref_view}').id, 'form')],
            'target': 'main',
        }
        return page
    
    def unlink(self):
        for record in self:
            if record.state == 'submitted':
                raise UserError("You cannot delete a purchase receipt that has been Posted.")
            
            reservation_entry = self.env['tms.reservation.entry'].search([
                ('source_type', '=', '39'),
                ('source_id', '=', self.document_no)
            ])
            reservation_entry.unlink()
            
        return super(TMSHandheldReceipt, self).unlink()
    
    @api.model
    def create(self, vals):
        if 'source_doc_no' in vals and vals['source_doc_no']:
            doctypesource = self.fnCheckDocTypeSource(vals)
            if self.document_type in ['1','2']:
                purchase_order = self.env['tms.purchase.order.header'].search([('no', '=', vals['source_doc_no']),('document_type','=',doctypesource)], limit=1)
                if not purchase_order:
                    raise ValidationError('Purchase Order not found.')
            elif self.document_type in ['3','4']:
                sales_order = self.env['tms.sales.order.header'].search([('no', '=', vals['source_doc_no']),('document_type','=',doctypesource)], limit=1)
                if not sales_order:
                    raise ValidationError('Sales Order not found.')

            self.fnCreateDocNo(vals)
        else:
            raise ValidationError('Source Doc. No. is required.')

        return super(TMSHandheldReceipt, self).create(vals)
    
    def fnCreateDocNo(self,vals) : 
        existing_trans = self.env['tms.handheld.transaction'].search([('source_doc_no', '=', vals['source_doc_no']),('document_type','=',vals["document_type"])],order = 'id desc',limit=1)
        if existing_trans:
            # trans_numbers = [
            #     int(trans.document_no.split('-')[-1]) for trans in existing_trans
            # ]
    
            max_trans_number = existing_trans.noseries_count
            vals['noseries_count'] = max_trans_number + 1
        else:
            vals['noseries_count'] = 1       

        if vals["document_type"] in ["1","4"] :
            title = "Receipt"
        elif vals["document_type"] in ["2","3"] :
            title = "Shipment"

        vals['document_no'] = f"{vals['source_doc_no']}-{title}-{vals['noseries_count']:03d}"

        return vals


    def scan_itemm(self):
        self.ensure_one()
        scan_item = self.env['tms.handheld.transaction.scan'].create({
            'handheld_transaction_id': self.id,
        })
        return {
            'name': 'Scan Item',
            'view_mode': 'form',
            'res_model': 'tms.handheld.transaction.scan',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': scan_item.id,
            'context': {
                'form_view_initial_mode': 'edit',
                'create': False, 'edit': True, 'delete': True
            }
        }
        
    def post(self):
        """
        This method will change the status of the receipt to 'Submitted' and change quantity in line to purchase order nav
        """
        url = f'http://{self.company.ip_or_url_api}:{self.company.port_api}/Thomasong/OData/Company(\'{self.company.name}\')/Handheld_Line_OData?$format=json'
        headers = {'Content-Type': 'application/json'}

        username = self.company.username_api
        password = self.company.password_api
        
        auth = HttpNtlmAuth(username, password)  # Using requests_ntlm2

        #clear line update on nav
        self.postHandheldTransAction("ClearUpdateLine")

        for line in self.transaction_line_ids:
            check_sn_info = False
            if line.item_no.sn_specific_tracking == True:
                check_sn_info = True
            elif line.item_no.sn_purchase_inbound_tracking == True:
                check_sn_info = True
            elif line.item_no.lot_specific_tracking == True:
                check_sn_info = True
            elif line.item_no.lot_purchase_inbound_tracking == True:
                check_sn_info = True

            newdocno = self.document_no
            doctype = self.fnCheckDocType()
            data = {
                "Document_Type": doctype,
                "Document_No": self.source_doc_no,
                "Line_No": str(line.line_no),
                "Quantity": str(line.qty_to_receive),
                "Processed_Header_ID": str(self.id),
                "Item_No": line.item_no.no,
                "External_Document_No" : str(self.vendor_shipment_no),
                "Handheld_Receipt_No" : str(newdocno),
                "Unit_Of_Measure_Code": line.item_uom.code
            }
            
            response = requests.post(url, headers=headers, auth=auth, json=data)
            
            if response.status_code == 400 :
                response_json = response.json()
                resp = response_json.get('odata.error', {}).get('message', {}).get('value', response.text )
                raise ValidationError( f'Nav Error {resp}')
            
            if line.item_no and (check_sn_info==True):
                self.handheld_sn(line.line_no)

        # #posting - send to transaction nav
        self.postHandheldTransAction("Purchase")

        purchase_order = self.env['tms.purchase.order.header'].search([('no', '=', self.source_doc_no)], limit=1)
        if not purchase_order:
            raise ValidationError('Related Purchase Order not found.')
        
    
        return {
            'name': 'Purchase Order',
            'view_mode': 'form',
            'res_model': 'tms.purchase.order.header',
            'type': 'ir.actions.act_window',
            'target': 'main',
            'res_id': purchase_order.id,
            'context': {
                'create': False, 'edit': False, 'delete': False
            }
        }
    
    def handheld_sn(self,line_no):
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
            ('source_id','=',self.document_no),('line_no','=',line_no)
        ])
        
        if reservation_entries:
            for entry in reservation_entries:
                receipt_line = self.env['tms.handheld.transaction.line'].search([
                    ('item_no.no', '=', entry.item_no),
                    ('handheld_transaction_id', '=', self.id)
                ], limit=1)
                
                # if not receipt_line:
                #     _logger.warning(f"No matching receipt line found for item {entry.item_no.id} in receipt {self.id}")
                #     continue
                
                data_sn = {
                    "Processed_Header_ID": str(self.id),
                    "Line_ID": str(receipt_line.id),
                    "Line_No": str(entry.line_no),
                    "Serial_No": entry.serial_no if entry.serial_no else "",
                    "Lot_No": entry.lot_no if entry.lot_no else "",
                    "Expired_Date": entry.expiration_date.isoformat() if entry.expiration_date else date.min.isoformat(),
                    "Quantity": str(entry.quantity),
                    "Document_Type" : self.document_type
                }
                
                response = requests.post(url, headers=headers, auth=auth, json=data_sn)
                
                if response.status_code == 400 :
                    response_json = response.json()
                    resp = response_json.get('odata.error', {}).get('message', {}).get('value', response.text )
                    raise ValidationError( f'Nav Error {resp}')
              
        else:
            raise UserError('No SN/LOT Detail')
        
    def postHandheldTransAction(self,parAction):
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

        doctype = self.fnCheckDocType()
      
        data2 = {
             'Document_Type': doctype,
             'Document_No': self.source_doc_no,
             "Processed_Header_ID": str(self.id),
             "Posting_Date": self.posting_date.isoformat(),
             'Post_Action': parAction,
             
        }

        response = requests.post(url2, headers=headers, auth=auth, json=data2)

        if response.status_code == 400 :
            response_json = response.json()
            resp = response_json.get('odata.error', {}).get('message', {}).get('value', response.text )
            raise ValidationError( f'Nav Error {resp}')
        elif response.status_code == 201 :
           self.state = 'submitted'
           message = f'Purchase Receive No. {self.document_no} succesfully Posted'
           self.fnCreateMessage(message)
                                 

    def fnCheckDocType(self) :
        if self.document_type == "1":
            doctype = "Purchase Order"
        elif self.document_type == "2":
            doctype = "Purchase Return"
        elif self.document_type  =="3":
            doctype = "Sales Order"
        elif self.document_type  == "4":
            doctype = "Sales  Return"

        return doctype
    
    def fnCheckDocTypeSource(self,vals) :
        if len(vals) == 0 :
            if self.document_type in ["1","3"]:
                doctype = "Order"
            elif self.document_type in ["2","4"]:
                doctype = "Return Order"
        else : 
            if vals["document_type"] in ["1","3"]:
                doctype = "Order"
            elif  vals["document_type"]  in ["2","4"]:
                doctype = "Return Order"

        return doctype

    def fnCreateMessage(self,message) :
        notification = {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': _('Warning'),
            'type': 'warning',
            'message': message,
            'sticky': True,
        }
        }
        return notification

    #Global Function
    def create_transaction(self,sourcno,docsource,doctype):
        if docsource == "Purchase" :
            if doctype == "Order" :
                doctype = "1"
                pagename = "Receipt"
            elif doctype == "Return Order" :
                doctype = "2"
                pagename = "Shipment"
        elif docsource == "Sales" :
            if doctype == "Order" :
                doctype = "3"
                pagename = "Shipment"
            elif doctype == "Return Order" :
                doctype = "4"
                pagename = "Receipt"
            
        trans_header = self.env['tms.handheld.transaction'].create({
            'source_doc_no': sourcno,
            'document_type':doctype
        })

        page = {
            'name': pagename,
            'view_mode': 'form',
            'res_model': 'tms.handheld.transaction',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': trans_header.id,
            'views': [(self.env.ref('tr_tms_handheld.purchase_receipt_2_view_form').id, 'form')],
            'context': {
                'create': True, 'edit': True, 'delete': True
            }
        }
        return page

    def view_transaction(self,sourcno,docsource,doctype):
        if docsource == "Purchase" :
            if doctype == "Order" :
                doctype = "1"
            elif doctype == "Return Order" :
                doctype = "2"
        elif docsource == "Sales" :
            if doctype == "Order" :
                doctype = "3"
            elif doctype == "Return Order" :
                doctype = "4"
               
        action = self.env.ref('tr_tms_handheld.action_receipt_po').read()[0]
        action['domain'] = [('source_doc_no', '=', sourcno),('document_type','=',doctype)]
        action['context'] = dict(self.env.context, create=False, edit=True)
        return action

class TMSHandheldTransactionLine(models.Model):
    _name = 'tms.handheld.transaction.line'
    _description = 'TMS Handheld Transaction Line'
    
    handheld_transaction_id = fields.Many2one('tms.handheld.transaction', string='Purchase Receipt', ondelete='cascade')
    # item_no = fields.Char('Item No.', readonly=True)
    line_no = fields.Integer('Line No.', store=True)
    item_no = fields.Many2one('tms.item', string="Item No.", domain="[('id', 'in', available_item_ids)]")
    description = fields.Char('Description', readonly=True, store=True)
    quantity = fields.Float('Quantity', readonly=True, store=True)
    # uom = fields.Char(string="Unit of Measure", readonly=True, store=True)
    item_uom = fields.Many2one('tms.item.uom', string="Unit of Measure", domain="[('item_no', '=', item_no_no)]")
    item_no_no = fields.Char(string='Item Number', store=True, related='item_no.no')
    qty_to_receive = fields.Float('Qty To Process', store=True)
    qty_received = fields.Float('Qty Processed')
    item_tracking_code = fields.Char(string='Item Tracking Code', related='item_no.item_tracking_code',store=True)
    available_item_ids = fields.Many2many('tms.item', compute='_compute_available_item_ids', store=False)
    
    @api.depends('handheld_transaction_id')
    def _compute_available_item_ids(self):
        """
        Domain Item. Get Item from Purchase Order"""
        for line in self:
            if line.handheld_transaction_id:
                purchase_order = self.env['tms.purchase.order.header'].search([
                    ('no', '=', line.handheld_transaction_id.source_doc_no)
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
        if self.item_no and self.handheld_transaction_id:
            purchase_order = self.env['tms.purchase.order.header'].search([
                ('no', '=', self.handheld_transaction_id.source_doc_no)
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

    @api.onchange('qty_to_receive')                
    def _onchange_qty_to_receive(self):
        if self.item_tracking_code:
            raise UserError('You cannot changes Qty to Process because there is SN/LOT Detail. You have to delete from SN/LOT Detail.')
       
    def action_view_reservation_entries(self):
        #Details
        self.ensure_one()
        action = self.env.ref('tr_tms_handheld.action_tms_reservation_entry').read()[0]
        
        action['domain'] = [('item_no', '=', self.item_no.no),('line_no', '=', self.line_no),
                            ('source_id', '=', self.handheld_transaction_id.document_no)]
        
        action['context'] = dict(self.env.context, create=False, edit=False,delete = True)
        
        return action
    
    def unlink(self):
        for line in self:
            # Search for the corresponding reservation entries
            reservation_entries = self.env['tms.reservation.entry'].search([
                ('item_no', '=', line.item_no.no),
                ('source_id', '=', line.handheld_transaction_id.document_no)
            ])
            # Delete the found reservation entries
            for re in reservation_entries : 
                re.unlink()
        
        # Call the super method to delete the purchase receipt line
        return super(TMSHandheldTransactionLine, self).unlink()

#dummy
class TmsReceiptHeader(models.Model):
    _name = 'tms.receipt.header'
    _description = 'TMS Receipt Header'
    _rec_name = 'no'

    document_type = fields.Char(string='Document Type', required=True)
    no = fields.Char(string='Receipt No.', required=True, default='New', readonly=True)



