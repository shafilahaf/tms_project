from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import requests
import logging
from requests_ntlm2 import HttpNtlmAuth
import json
from datetime import date
import xml.etree.ElementTree as ET
import re

_logger = logging.getLogger(__name__)
class TmsItemIdentifiers(models.Model):
    _name = 'tms.item.identifiers'
    _description = 'TMS Item Identifiers'
    _rec_name = 'item_no'

    item_no = fields.Many2one('tms.item', string='Item')
    variant_code = fields.Many2one('tms.item.variant', string='Variant Code', domain="[('item_no', '=', item_no)]")
    unit_of_measure_code = fields.Many2one('tms.unit.of.measures', string='Unit of Measures')
    barcode_type = fields.Selection([
        ('1', 'GSI 128'),
        ('2','Code 39'),
        ('3', 'QR')
    ], string='Barcode type', required=True)
    barcode_code = fields.Char(string="Barcode Code", store=True)
    blocked = fields.Boolean(strinng="Blocked")
    entry_no = fields.Integer(string="Entry No")

    @api.onchange('item_no')
    def _onchange_item_no(self):
        if self.item_no:
            base_unit_of_measure_id = self.item_no.base_unit_of_measure_id
            return {'domain': {'unit_of_measure_code': [('code', '=', base_unit_of_measure_id)]}}
        else:
            # Clear the domain if no item is selected
            return {'domain': {'unit_of_measure_code': []}}

    @api.model
    def create(self, vals):
        record = super(TmsItemIdentifiers, self).create(vals)
        record.create_item_identifiers()
        
        return record

    def write(self, vals):
        res = super(TmsItemIdentifiers, self).write(vals)
        
        for record in self:
            record.update_item_identifier(record.entry_no)

        return res
    

    def retrieve_etag(self, entryno):
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodes(Entry_No={int(entryno)})?$format=json'
        
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
        
    def update_item_identifier(self, entryno):
        etag = self.retrieve_etag(entryno)
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodes(Entry_No={int(entryno)})?$format=json'
        headers = {'Content-Type': 'application/json', 'If-Match': etag}

        username = current_company.username_api
        password = current_company.password_api

        data = {
            "Barcode_Type": self.barcode_type,
            "Barcode_Code": self.barcode_code,
            "Variant_Code": self.variant_code.code if self.variant_code else "",
            "Blocked": True if self.blocked == True else False,
            "Entry_No": self.entry_no,
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

    def create_item_identifiers(self):
        current_company = self.env.user.company_id
        url2 = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodes?$format=json'
        headers = {'Content-Type': 'application/json'}

        username = current_company.username_api
        password = current_company.password_api
        
        auth = HttpNtlmAuth(username, password)  # Using requests_ntlm2

        blocked = False
        if self.blocked == True:
            blocked = True

        data2 = {
             'Item_No': self.item_no.no,
             'Variant_Code': self.variant_code.code if self.variant_code else "",
             "Barcode_Code": self.barcode_code,
             'Unit_Of_Measure_Code': self.unit_of_measure_code.code,
             "Barcode_Type": self.barcode_type,
             "Blocked": blocked,
        }
        try:
            response = requests.post(url2, headers=headers, auth=auth, json=data2)
            response.raise_for_status()

            response_json = response.json()
            entry_no = response_json.get("Entry_No")

            if entry_no:
                self.entry_no = entry_no
        except requests.exceptions.HTTPError as e:
            try:
                root = ET.fromstring(response.text)
                error_message = root.find('.//m:message', {'m': 'http://schemas.microsoft.com/ado/2007/08/dataservices/metadata'}).text
            except ET.ParseError:
                error_message = response.text  # Fallback to the full response text if XML parsing fails
            _logger.error(f"HTTP error occurred while create item idenfirers: {error_message}")
            raise UserError(error_message)
        except requests.exceptions.RequestException as e:
            error_message = f"HTTP error occurred: {str(e)}"
            _logger.error(error_message)
            raise UserError(error_message)
        except ValueError as e:
            error_message = f"JSON encode error: {str(e)} {data2}"
            _logger.error(error_message)
            raise UserError(error_message)
        
    # barcode split
    @api.onchange('barcode_code', 'barcode_type')
    def _onchange_barcode_code(self):
        if self.barcode_code:
            if self.barcode_type == '1' or self.barcode_type == '3':
                self.barcode_code = self.extract_value_for_key_01(self.process_barcode(self.barcode_code))

    def process_barcode(self, barcode):
        """Process the barcode according to GS1-128 standards."""
        new_array_barcode = []

        gs1_128_length_dict = {
            '01': 14,
            '10': 4,
            '11': 6,
            '13': 6,
            '15': 6,
            '17': 6
        }

        gs1_128_separator = [10, 23, 21, 11, 13, 15, 17]

        def check_gs1_128_1(barcode):
            two_digit_first = barcode[:2]
            return two_digit_first in gs1_128_length_dict

        def check_gs1_128_1_1(barcode):
            two_digit_first = barcode[:2]
            length = gs1_128_length_dict.get(two_digit_first, 0)
            if length:
                barcode_group = barcode[:2+length]
                new_array_barcode.append({barcode_group[:2]: barcode_group[2:]})
                new_barcode = barcode[length+2:]  # Skip the length of the matched segment
                return new_barcode
            return barcode

        def regex_gs1_128(digit_first, key, barcode):
            regex = f"{digit_first}(\w+?)(?:{key})"
            matches = re.finditer(regex, barcode)
            for match in matches:
                return match.group(1)
            return ''

        def check_gs1_128_2(barcode):
            two_digit_first = barcode[:2]
            regex_save = ''
            for key2 in gs1_128_separator:
                if two_digit_first != str(key2):
                    regex_barcode = regex_gs1_128(two_digit_first, key2, barcode)
                    if regex_barcode:
                        if not regex_save or len(regex_barcode) > len(regex_save[2:]):
                            regex_save = two_digit_first + regex_barcode
            if not regex_save:
                barcode_group = barcode
                new_array_barcode.append({barcode_group[:2]: barcode_group[2:]})
            else:
                barcode_group = regex_save
                new_array_barcode.append({barcode_group[:2]: barcode_group[2:]})

            new_barcode = barcode[len(barcode_group):]
            return new_barcode

        barcode_2 = barcode
        while barcode_2:
            if check_gs1_128_1(barcode_2):
                barcode_2 = check_gs1_128_1_1(barcode_2)
            else:
                barcode_2 = check_gs1_128_2(barcode_2)

        return new_array_barcode

    def extract_value_for_key_01(self, barcode_array):
        """Extract the value corresponding to key '01'."""
        for item in barcode_array:
            if '01' in item:
                return item['01']
        return self.barcode_code  # Keep the original if '01' is not found
    
    
    # barcode split