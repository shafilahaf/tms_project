from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import requests
import logging
from requests_ntlm2 import HttpNtlmAuth

_logger = logging.getLogger(__name__)

class TmsItemVariant(models.Model):
    _name = 'tms.item.variant'
    _description = 'TMS Item Variant'
    _rec_name = 'code'

    guid = fields.Char('GUID NAV')
    code = fields.Char(string='Code', required=True)
    item_no = fields.Many2one('tms.item', string='Item', required=True)
    description = fields.Text(string='Description')
    description_2 = fields.Text(string='Description 2')
    barcode_type_id = fields.Selection([
        ('1', 'GSI 128'),
        ('2','Code 39'),
        ('3', 'QR')
    ], string='Barcode type')
    barcode_code = fields.Char('Barcode Code')
    
    def write(self, vals):
        res = super(TmsItemVariant, self).write(vals)
        
        if 'barcode_type_id' in vals or 'barcode_code' in vals:
            for record in self:
                if record.code and record.item_no:
                    record.update_barcode_type_and_code(record.item_no.no, record.code)

        return res
    
    def retrieve_etag(self, itemno, code):
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/Item_Variants(Item_No=\'{itemno}\', Code=\'{code}\')?$format=json'
        
        headers = {'Content-Type': 'application/json'}
        
        username = current_company.username_api
        password = current_company.password_api
        
        try:
            auth = HttpNtlmAuth(username, password)
            response = requests.get(url, headers=headers, auth=auth)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            
            # Retrieve etag from response headers
            etag = response.headers.get('ETag')
            if not etag:
                _logger.error("ETag not found in response headers")
                raise UserError("ETag not found in response headers")

            return etag

        except requests.exceptions.RequestException as e:
            _logger.error(f"HTTP error occurred: {e}")
            raise UserError(f"HTTP error occurred: {e}")
        except ValueError as e:
            _logger.error(f"JSON decode error: {e}")
            _logger.error(f"Response content: {response.text}")
            raise UserError(f"JSON decode error: {e}")

    
    def update_barcode_type_and_code(self, itemno, code):
        etag = self.retrieve_etag(itemno, code)
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/Item_Variants(Item_No=\'{itemno}\',Code=\'{code}\')?$format=json'
        headers = {'Content-Type': 'application/json', 'If-Match': etag}

        username = current_company.username_api
        password = current_company.password_api

        data = {
            "Barcode_Type": self.barcode_type_id,
            "Barcode_Code": self.barcode_code
        }

        try:
            auth = HttpNtlmAuth(username, password)
            response = requests.patch(url, headers=headers, auth=auth, json=data)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            _logger.debug(f"Response Status Code: {response.status_code}")
            _logger.debug(f"Response Headers: {response.headers}")
            _logger.debug(f"Response Content: {response.content}")
        except requests.exceptions.RequestException as e:
            _logger.error(f"HTTP error occurred: {e}")
            raise UserError(f"HTTP error occurred: {e}")
        except ValueError as e:
            _logger.error(f"JSON decode error: {e}")
            _logger.error(f"Response content: {response.text}")
            raise UserError(f"JSON decode error: {e}")
