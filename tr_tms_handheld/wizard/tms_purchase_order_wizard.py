from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import requests
import logging
# from requests_ntlm2 import HttpNtlmAuth

_logger = logging.getLogger(__name__)
class TMSPurchaseOrderWizard(models.TransientModel):
    _name = 'tms.purchase.order.wizard'
    _description = 'TMS Purchase Order Wizard'

    description = fields.Char(string='Description', required=True, default='This is wizard for syncing purchase order from NAV to Odoo')
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)

    
    def get_purchase_header(self):
        url = f'http://{self.company.ip_or_url_api}:{self.company.port_api}/Thomasong/OData/Company(\'{self.company.name}\')/PurchaseOrders?$format=json'
        headers = {'Content-Type': 'application/json'}

        username = self.company.username_api
        password = self.company.password_api

        try:
            auth = HttpNtlmAuth(username, password)
            response = requests.get(url, headers=headers, auth=auth)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            _logger.debug(f"Response Status Code: {response.status_code}")
            _logger.debug(f"Response Headers: {response.headers}")
            _logger.debug(f"Response Content: {response.content}")

            data = response.json()
        except requests.exceptions.RequestException as e:
            _logger.error(f"HTTP error occurred: {e}")
            raise UserError(f"HTTP error occurred 1: {e}")
        except ValueError as e:
            _logger.error(f"JSON decode error: {e}")
            _logger.error(f"Response content: {response.text}")
            raise UserError(f"JSON decode error: {e}")

        if 'value' in data:
            tms_purchase = self.env['tms.purchase.order.header']
            for po in data['value']:
                purchase_no = tms_purchase.search([('document_type', '=', po['Document_Type']), ('no', '=', po['No'])])
                if not purchase_no:
                    tms_purchase.create({
                        'document_date': po['Document_Date'],
                        'document_type': po['Document_Type'],
                        'no': po['No'],
                        'vendor_no': po['Buy_from_Vendor_No'],
                        'vendor_name': po['Buy_from_Vendor_Name'],
                        'etag': po['ETag']
                    })
                else:
                    purchase_no.write({
                        'document_date': po['Document_Date'],
                        'document_type': po['Document_Type'],
                        'vendor_no': po['Buy_from_Vendor_No'],
                        'vendor_name': po['Buy_from_Vendor_Name'],
                        'etag': po['ETag']
                    })
                self.get_purchase_lines(po['Document_Type'], po['No'])
                self.create_po_unchecklist(po['Document_Type'], po['No'])
                
        else:
            raise UserError('No data found in response')
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Order'),
            'res_model': 'tms.purchase.order.header',
            'view_mode': 'tree,form',
            'domain': [],
            'context': {},
        }
    
    def get_purchase_lines(self, doc_type, doc_no):
        url = f'http://{self.company.ip_or_url_api}:{self.company.port_api}/Thomasong/OData/Company(\'{self.company.name}\')/PurchaseLines?$filter=(Document_Type eq \'{doc_type}\') and (Document_No eq \'{doc_no}\')&$format=json'
        headers = {'Content-Type': 'application/json'}

        username = self.company.username_api
        password = self.company.password_api

        try:
            auth = HttpNtlmAuth(username, password)
            response = requests.get(url, headers=headers, auth=auth)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            _logger.debug(f"Response Status Code: {response.status_code}")
            _logger.debug(f"Response Headers: {response.headers}")
            _logger.debug(f"Response Content: {response.content}")

            data = response.json()
        except requests.exceptions.RequestException as e:
            _logger.error(f"HTTP error occurred: {e}")
            raise UserError(f"HTTP error occurred: {e}")
        except ValueError as e:
            _logger.error(f"JSON decode error: {e}")
            _logger.error(f"Response content: {response.text}")
            raise UserError(f"JSON decode error: {e}")

        if 'value' in data:
            tms_purchase_line = self.env['tms.purchase.order.line']
            purchase_line_no = tms_purchase_line.search([('document_type', '=', doc_type), ('document_no', '=', doc_no)])
            purchase_line_no.unlink()
            for pol in data['value']:
                tms_purchase_line.create({
                    'document_type': pol['Document_Type'],
                    'document_no': pol['Document_No'],
                    'header_id': self.env['tms.purchase.order.header'].search([('document_type', '=', pol['Document_Type']), ('no', '=', pol['Document_No'])]).id,
                    'line_no': pol['Line_No'],
                    'item_no': pol['No'],
                    'location': pol['Location_Code'],
                    'qty': pol['Quantity'],
                    'uom': pol['Unit_of_Measure'],
                    'qty_to_receive': pol['Qty_to_Receive'],
                    'qty_received': pol['Quantity_Received'],
                    'etag': pol['ETag'],
                    'item_description': pol['Description']
                })         
        else:
            raise UserError('No data found in response')


    def create_po_unchecklist(self, doc_type ,doc_no):
        # url = f'http://{self.company.ip_or_url_api}:{self.company.port_api}/Thomasong/OData/Company(\'{self.company.name}\')/PurchaseOrders?$format=json'
        url = f'http://{self.company.ip_or_url_api}:{self.company.port_api}/Thomasong/OData/Company(\'{self.company.name}\')/POArch?$format=json'
        headers = {'Content-Type': 'application/json'}

        username = self.company.username_api
        password = self.company.password_api

        data = {
             'Document_Type': doc_type,
             'No': doc_no,
             'Doc_No_Occurrence': "1",
             'Version_No': "0",
             'WMS_Code': "1",
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
            raise UserError(f"HTTP error occurred 2: {e}")
        except ValueError as e:
            _logger.error(f"JSON decode error: {e}")
            _logger.error(f"Response content: {response.text}")
            raise UserError(f"JSON decode error: {e}")