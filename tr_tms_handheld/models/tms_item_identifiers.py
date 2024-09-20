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
    item_identifiers_line_ids = fields.One2many('tms.item.identifiers.line', 'header_id', string='Item Identifier Line')

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

    # barcode split 2
    @api.onchange('barcode_code', 'barcode_type')
    def _onchange_barcode_code(self):
        """
        This method is triggered when the barcode_code or barcode_type field is changed.
        It parses the GS1-128 barcode if the type is GS1-128, and automatically updates the item and variant fields.
        """
        if self.barcode_code and self.barcode_type == '1':  
            try:
                # barcode parsing method for GS1-128
                parsed_data = self.parse_gs1_128_barcode(self.barcode_code)

                gtin = parsed_data.get('01')

                if gtin:
                    self.barcode_code = gtin

            except Exception as e:
                raise ValidationError(f"Error parsing GS1-128 barcode: {str(e)}")

    def parse_gs1_128_barcode(self, barcode):
        """
        Parses a GS1-128 barcode, handling FNC1 separators and extracting AI data.
        """
        # GS1-128 FNC1 separator is ASCII 29 or \x1D
        fnc1_separator = '\x1D'
        
        # Replace FNC1 separator with something easier to handle or remove it
        barcode = barcode.replace(fnc1_separator, '')

        # Application Identifiers and their expected fixed lengths
        fixed_length_ai = {
            '00': 18,  # Serial Shipping Container Code (SSCC)
            '01': 14,  # Global Trade Item Number (GTIN)
            '02': 14,  # GTIN of contained trade items
            '11': 6,   # Production date (YYMMDD)
            '12': 6,   # Due date (YYMMDD)
            '13': 6,   # Packaging date (YYMMDD)
            '15': 6,   # Best before date (YYMMDD)
            '16': 6,   # Sell by date (YYMMDD)
            '17': 6,   # Expiration date (YYMMDD)
            '20': 2,   # Internal product variant
        }

        # Variable-length AI definitions (delimited by FNC1)
        variable_length_ai = {
            '10': 20,  # Batch or lot number
            '21': 20,  # Serial number
            '22': 20,  # Consumer product variant
            '235': 28, # Third Party Controlled, Serialised Extension of GTIN (TPX)
            '240': 30, # Additional product identification assigned by the manufacturer
            '241': 30, # Customer part number
            '242': 6,  # Made-to-Order variation number
            '243': 20, # Packaging component number
            '250': 30, # Secondary serial number
            '251': 30, # Reference to source entity
            '253': 30, # Global Document Type Identifier (GDTI) - variable format
            '254': 20, # GLN extension component
            '255': 25, # Global Coupon Number (GCN) - variable format
            '30': 8,   # Variable count of items (variable measure trade item)
        }

        ai_data = {}
        index = 0

        while index < len(barcode):
            ai = barcode[index:index + 2]
            if ai in ['253', '255']:  # Handle the 3-digit AIs
                ai = barcode[index:index + 3]
                index += 3
            else:
                index += 2

            if ai in fixed_length_ai:
                length = fixed_length_ai[ai]
                value = barcode[index:index + length]
                index += length
                ai_data[ai] = value
            elif ai in variable_length_ai:
                max_length = variable_length_ai[ai]

                fnc1_pos = barcode.find(fnc1_separator, index)
                if fnc1_pos == -1:
                    value = barcode[index:index + max_length]
                    index += len(value)
                else:
                    value = barcode[index:fnc1_pos]
                    index = fnc1_pos + 1

                ai_data[ai] = value
            else:
                raise ValidationError(f"Unknown Application Identifier (AI): {ai}")

        return ai_data
    # barcode split 2


class TMSItemIdentifierLine(models.Model):
    _name = 'tms.item.identifiers.line'
    _description = 'TMS Item Identifiers Line'

    header_id = fields.Many2one('tms.item.identifiers', string='Header', ondelete='cascade')
    sequence = fields.Integer(string="Sequence")
    gs1_identifier = fields.Char(string="GS1 Identifier")
    description = fields.Char(string="Description")
    data_length = fields.Integer(string="Data Length")

