from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import requests
import logging
# from requests_ntlm2 import HttpNtlmAuth
import logging

_logger = logging.getLogger(__name__)
class TmsReceiptHeader(models.Model):
    _name = 'tms.receipt.header'
    _description = 'TMS Receipt Header'
    _rec_name = 'no'

    document_type = fields.Char(string='Document Type', required=True)
    no = fields.Char(string='Receipt No.', required=True, default='New', readonly=True)
    refer_to_doc_no = fields.Char(string='Refer to Doc No.')
    refer_to_doc_type = fields.Char(string='Refer to Doc Type')
    document_date = fields.Date(string='Document Date')
    status = fields.Selection([
        ('open', 'Open'),
        ('submitted', 'Submitted'),
    ], string='Status', default='open', readonly=True)
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)

    receipt_line_ids = fields.One2many('tms.receipt.line', 'header_id', string='Receipt Lines')
    

    @api.model
    def create(self, vals):
        if vals.get('no', 'New') == 'New':
            vals['no'] = self.env['ir.sequence'].next_by_code('tms.receipt.header') or 'New'
        return super(TmsReceiptHeader, self).create(vals)
    
    def scan_receipt(self):
        # Create a new record for the receipt detail
        receipt_detail = self.env['tms.receipt.detail.header'].create({
            'document_type': self.document_type,
            'document_date': self.document_date,
            'no': self.no,
            'related_doc_no': self.refer_to_doc_no,
        })
        # Open the receipt detail form view in edit mode

        context = dict(self.env.context)
        context['form_view_initial_mode'] = 'edit'
        return {
            'type': 'ir.actions.act_window',
            'name': 'Receipt Detail',
            'view_mode': 'form',
            'res_model': 'tms.receipt.detail.header',
            'res_id': receipt_detail.id,
            'target': 'current',  # or 'new' to open in a new window
            # 'context': self.env.context,
            'context': context,
        }


    def submit_receipt(self):
        self.create_po_archive_header(self.document_type, self.refer_to_doc_no)
        self.create_po_archive_line()
        self.posting_receipt(self.document_type, self.refer_to_doc_no)
        # self.status = 'submitted'
        
    def create_po_archive_header(self, doc_type, doc_no):
        url = f'http://{self.company.ip_or_url_api}:{self.company.port_api}/Thomasong/OData/Company(\'{self.company.name}\')/POArch?$format=json'
        headers = {'Content-Type': 'application/json'}

        username = self.company.username_api
        password = self.company.password_api

        data = {
             'Document_Type': doc_type,
             'No': doc_no,
             'Doc_No_Occurrence': "1",
             'Version_No': "0",
             'WMS_Code': "2", # Write
        }

        try:
            auth = HttpNtlmAuth(username, password)
            response = requests.post(url, headers=headers, auth=auth, json=data)
            response.raise_for_status()  # Raise an HTTPError for bad responses

            # self.create_po_archive_line()

            _logger.debug(f"Response Status Code: {response.status_code}")
            _logger.debug(f"Response Headers: {response.headers}")
            _logger.debug(f"Response Content: {response.content}")
        except requests.exceptions.RequestException as e:
            _logger.error(f"HTTP error occurred: {e}")
            raise UserError(f"HTTP error occurred 2: {e}")
        except ValueError as e:
            _logger.error(f"JSON decode error: {e}")
            _logger.error(f"Response content: {response.text}")
            raise UserError(f"JSON decode error: {e}")

    def create_po_archive_line(self):
        """
        This method will change the status of the receipt to 'Submitted' and change quantity in line to purchase order nav
        """
        url = f'http://{self.company.ip_or_url_api}:{self.company.port_api}/Thomasong/OData/Company(\'{self.company.name}\')/POLArch?$format=json'
        headers = {'Content-Type': 'application/json'}

        username = self.company.username_api
        password = self.company.password_api

        for line in self.receipt_line_ids:
            data = {
             'Document_Type': self.document_type,
             'Document_No': self.refer_to_doc_no,
             'Doc_No_Occurrence': "1",
             'Version_No': "0",
             'Type' : "Item",
             'No': line.item_no,
             'Line_No': line.line_no,
             'Quantity': str(line.quantity),
             'Unit_of_Measure': line.uom,
             'WMS_Code': "2", # Write
            }


            try:
                auth = HttpNtlmAuth(username, password)
                response = requests.post(url, headers=headers, auth=auth, json=data)
                response.raise_for_status()  # Raise an HTTPError for bad responses
                _logger.debug(f"Response Status Code: {response.status_code}")
                _logger.debug(f"Response Headers: {response.headers}")
                _logger.debug(f"Response Content: {response.content}")
            except requests.exceptions.RequestException as e:
                _logger.error(f"HTTP error occurred: {e}")
                raise UserError(f"HTTP error occurred 2: {e}{data}")
            except ValueError as e:
                _logger.error(f"JSON decode error: {e}")
                _logger.error(f"Response content: {response.text}")
                raise UserError(f"JSON decode error: {e}")
            
    def posting_receipt(self, doc_type, doc_no):
        url = f'http://{self.company.ip_or_url_api}:{self.company.port_api}/Thomasong/OData/Company(\'{self.company.name}\')/POArch?$format=json'
        headers = {'Content-Type': 'application/json'}

        username = self.company.username_api
        password = self.company.password_api

        data = {
             'Document_Type': doc_type,
             'No': doc_no,
             'Doc_No_Occurrence': "1",
             'Version_No': "0",
             'Vendor_Shipment_No': self.no,
             'WMS_Code': "3", #Posting
        }

        try:
            auth = HttpNtlmAuth(username, password)
            response = requests.post(url, headers=headers, auth=auth, json=data)
            response.raise_for_status()  # Raise an HTTPError for bad responses

            # self.create_po_archive_line()

            _logger.debug(f"Response Status Code: {response.status_code}")
            _logger.debug(f"Response Headers: {response.headers}")
            _logger.debug(f"Response Content: {response.content}")
        except requests.exceptions.RequestException as e:
            _logger.error(f"HTTP error occurred: {e}")
            raise UserError(f"HTTP error occurred 2: {e}")
        except ValueError as e:
            _logger.error(f"JSON decode error: {e}")
            _logger.error(f"Response content: {response.text}")
            raise UserError(f"JSON decode error: {e}")


class TmsReceiptLine(models.Model):
    _name = 'tms.receipt.line'
    _description = 'TMS Receipt Line'

    header_id = fields.Many2one('tms.receipt.header', string='Header', required=True, ondelete='cascade')
    document_type = fields.Char(string='Document Type', required=True, store=True, related='header_id.document_type')
    document_no = fields.Char(string='Document No.', required=True, store=True, related='header_id.no')
    line_no = fields.Integer(string='Line No.', required=True)
    item_no = fields.Char(string='Item No.', required=True)
    quantity = fields.Float(string='Quantity')
    uom = fields.Char(string='UOM')
    item_description = fields.Char(string='Item Description')

