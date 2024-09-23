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
    need_sent_to_wms = fields.Boolean(string="Need Sent to WMS")
    from_nav = fields.Boolean(string="From NAV", default=False)

    # SH
    sh_product_barcode_mobile = fields.Char(string="Mobile Barcode", store=True)   
    # SH

    @api.onchange('item_no')
    def _onchange_item_no(self):
        if self.item_no:
            base_unit_of_measure_id = self.item_no.base_unit_of_measure_id
            return {'domain': {'unit_of_measure_code': [('code', '=', base_unit_of_measure_id)]}}
        else:
            # Clear the domain if no item is selected
            return {'domain': {'unit_of_measure_code': []}}

    # @api.model
    # def create(self, vals):
    #     record = super(TmsItemIdentifiers, self).create(vals)
    #     if not 'from_nav' in vals:
    #         record.create_item_identifiers()
        
    #     return record

    # def write(self, vals):
    #     res = super(TmsItemIdentifiers, self).write(vals)
        
    #     for record in self:
    #        if not 'from_nav' in vals:
    #            record.create_item_identifiers()

    #     return res
    
    def unlink(self):
        self.delete_item_identifier(self.retrieve_etag(self.entry_no), self.entry_no)
        # Proceed with the standard unlink process
        return super(TmsItemIdentifiers, self).unlink()

    def delete_item_identifier(self, etag, entryno):
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodes(Entry_No={int(entryno)})?$format=json'
        headers = {'Content-Type': 'application/json', 'If-Match': etag}

        username = current_company.username_api
        password = current_company.password_api
        try:
            auth = HttpNtlmAuth(username, password)
            response = requests.delete(url, headers=headers, auth=auth)
            # # # response.raise_for_status()  # Raise an HTTPError for bad responses
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

        
    def check_blocked(self):
        for rec in self:
            current_company = self.env.user.company_id
            url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodes(Entry_No={int(self.entry_no)})?$format=json'
            headers = {'Content-Type': 'application/json', 'If-Match': rec.retrieve_etag(self.entry_no)}

            username = current_company.username_api
            password = current_company.password_api

            data = {
                "Blocked": True if self.blocked == True else False,
            }

            try:
                auth = HttpNtlmAuth(username, password)
                response = requests.patch(url, headers=headers, auth=auth, json=data)
                # # response.raise_for_status()  # Raise an HTTPError for bad responses
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
            
            rec.blocked = True


    def retrieve_etag(self, entryno):
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodes(Entry_No={int(entryno)})?$format=json'
        
        headers = {'Content-Type': 'application/json'}
        
        username = current_company.username_api
        password = current_company.password_api
        
        try:
            auth = HttpNtlmAuth(username, password)
            response = requests.get(url, headers=headers, auth=auth)
            # # response.raise_for_status()  # Raise an HTTPError for bad responses
            
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
        
    def create_item_identifiers(self):
       
        # Retrieve etag from response headers
        if not self.entry_no:
            self.post_item_identifier()
        else:
            self.update_item_identifier(self.entry_no, blocked=False)
     
        self.create_item_line_idenfitiers()
    
    def update_item_identifier(self, entryno, blocked):
        etag = self.retrieve_etag(entryno)
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodes(Entry_No={int(self.entry_no)})?$format=json'
        headers = {'Content-Type': 'application/json', 'If-Match': etag}

        username = current_company.username_api
        password = current_company.password_api

        data = {
            "Barcode_Type": self.barcode_type,
            "Barcode_Code": self.sh_product_barcode_mobile,
            "Variant_Code": self.variant_code.code if self.variant_code else "",
            "Blocked": True if self.blocked == True else False,
            "Entry_No": self.entry_no,
            "Need_Sent_to_WMS": False
        }

        try:
            auth = HttpNtlmAuth(username, password)
            response = requests.patch(url, headers=headers, auth=auth, json=data)
            # # response.raise_for_status()  # Raise an HTTPError for bad responses
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

    def post_item_identifier(self):
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
             "Barcode_Code": self.sh_product_barcode_mobile,
             'Unit_Of_Measure_Code': self.unit_of_measure_code.code,
             "Barcode_Type": self.barcode_type,
             "Need_Sent_to_WMS": False,
        }
        try:
            response = requests.post(url2, headers=headers, auth=auth, json=data2)
            # # response.raise_for_status()

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
    
    
    # barcode split 2
    @api.onchange('sh_product_barcode_mobile', 'barcode_type')
    def _onchange_sh_product_barcode_mobile(self):
        if self.sh_product_barcode_mobile and self.barcode_type == '1':  
            try:
                # barcode parsing method for GS1-128
                parsed_data = self.parse_gs1_128_barcode(self.sh_product_barcode_mobile)
                self.sh_product_barcode_mobile = parsed_data

            except Exception as e:
                raise ValidationError(f"Error parsing GS1-128 barcode: {str(e)}")

    def parse_gs1_128_barcode(self, barcode):
        if barcode[:2] == "01":
            digit_first_14 = barcode[2:13]
            new_barcode= digit_first_14
        else:
            new_barcode = barcode
        
        return new_barcode
    # barcode split 2

    # Line
    def create_item_line_idenfitiers(self):
        for line in self.item_identifiers_line_ids:
            current_company = self.env.user.company_id
            url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodesDetail(Source_Entry_No={self.entry_no},Sequence={line.sequence})?$format=json'
            
            headers = {'Content-Type': 'application/json'}
            
            username = current_company.username_api
            password = current_company.password_api

            auth = HttpNtlmAuth(username, password)
            response = requests.get(url, headers=headers, auth=auth)

            if response.status_code == 200:
                etag = response.headers.get('ETag')
                self.update_item_line_identifier(etag, self.entry_no, line.sequence, line.gs1_identifier, line.description, line.data_length, line.blocked)
            else:
                self.post_item_line_identifiers(line.sequence, line.gs1_identifier, line.description, line.data_length)

    def post_item_line_identifiers(self, sequence, gs1_iden, description, length):
        current_company = self.env.user.company_id
        url2 = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodesDetail?$format=json'
        headers = {'Content-Type': 'application/json'}

        username = current_company.username_api
        password = current_company.password_api
        
        auth = HttpNtlmAuth(username, password)  # Using requests_ntlm2
        data2 = {
            "Source_Entry_No": self.entry_no,
            "Sequence": sequence,
            "GS1_Identifier": gs1_iden,
            "Description": description,
            "Data_Length": length,
            "Need_Sent_to_WMS": False,
        }
        try:

            response = requests.post(url2, headers=headers, auth=auth, json=data2)
            # response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            try:
                root = ET.fromstring(response.text)
                error_message = root.find('.//m:message', {'m': 'http://schemas.microsoft.com/ado/2007/08/dataservices/metadata'}).text
            except ET.ParseError:
                error_message = response.text
            _logger.error(f"HTTP error occurred while creating line identifiers: {error_message}")
            raise UserError(error_message)
        except requests.exceptions.RequestException as e:
            _logger.error(f"HTTP error occurred: {str(e)}")
            raise UserError(f"HTTP error occurred: {str(e)}")
        
    def update_item_line_identifier(self, etag, entryno, seq, gs1_ident,description,length,blocked):
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodesDetail(Source_Entry_No={int(entryno)},Sequence={int(seq)})?$format=json'
        headers = {'Content-Type': 'application/json', 'If-Match': etag}

        username = current_company.username_api
        password = current_company.password_api

        data = {
            'GS1_Identifier': gs1_ident,
            'Description': description,
            'Data_Length': length,
            'Need_Sent_to_WMS': False

        }

        try:
            auth = HttpNtlmAuth(username, password)
            response = requests.patch(url, headers=headers, auth=auth, json=data)
            # # response.raise_for_status()  # Raise an HTTPError for bad responses
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
        
    
    # Line

class TMSItemIdentifierLine(models.Model):
    _name = 'tms.item.identifiers.line'
    _description = 'TMS Item Identifiers Line'

    header_id = fields.Many2one('tms.item.identifiers', string='Header', ondelete='cascade')
    sequence = fields.Integer(string="Sequence")
    gs1_identifier = fields.Char(string="GS1 Identifier")
    description = fields.Char(string="Description")
    data_length = fields.Integer(string="Data Length")
    need_sent_to_wms = fields.Boolean(string="Need Sent to WMS")
    blocked = fields.Boolean(string="Blocked")

    @api.onchange('header_id')
    def _onchange_header_id(self):
        if self.header_id:
            # Get the next sequence number for the selected header
            existing_lines = self.search([('header_id', '=', self.header_id.id)], order="sequence desc", limit=1)
            if existing_lines:
                self.sequence = existing_lines.sequence + 1
            else:
                self.sequence = 1

    def check_line_blocked(self):
        for record in self:
            entry_no = record.header_id.entry_no
            sequence = record.sequence
            blocked = record.blocked

            current_company = self.env.user.company_id
            url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodesDetail(Source_Entry_No={int(entry_no)},Sequence={int(sequence)},Blocked={str(blocked).lower()})?$format=json'
            headers = {'Content-Type': 'application/json', 'If-Match': record.retrieve_line_etag(entry_no, sequence, blocked)}

            username = current_company.username_api
            password = current_company.password_api

            data = {
                'Blocked':True,
            }

            try:
                auth = HttpNtlmAuth(username, password)
                response = requests.patch(url, headers=headers, auth=auth, json=data)
                # # response.raise_for_status()  # Raise an HTTPError for bad responses
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
            
            
            record.unlink()

    def unlink(self):
        self.delete_item_line_identifier(self.retrieve_line_etag(self.header_id.entry_no, self.sequence), self.header_id.entry_no,self.sequence)
        # Proceed with the standard unlink process
        return super(TMSItemIdentifierLine, self).unlink()

    def delete_item_line_identifier(self, etag, entryno, seq):
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodesDetail(Source_Entry_No={int(entryno)},Sequence={int(seq)})?$format=json'
        headers = {'Content-Type': 'application/json', 'If-Match': etag}

        username = current_company.username_api
        password = current_company.password_api
        try:
            auth = HttpNtlmAuth(username, password)
            response = requests.delete(url, headers=headers, auth=auth)
            # # # response.raise_for_status()  # Raise an HTTPError for bad responses
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
        
    def retrieve_line_etag(self, entryno, sequence):
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodesDetail(Source_Entry_No={int(entryno)},Sequence={int(sequence)})?$format=json'
        
        headers = {'Content-Type': 'application/json'}
        
        username = current_company.username_api
        password = current_company.password_api
        
        try:
            auth = HttpNtlmAuth(username, password)
            response = requests.get(url, headers=headers, auth=auth)
            # # response.raise_for_status()  # Raise an HTTPError for bad responses
            
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
    # def write(self, vals):
    #     for record in self:
    #         entry_no = record.header_id.entry_no
    #         sequence = record.sequence
    #         blocked = record.blocked

    #         res = super(TMSItemIdentifierLine, record).write(vals)

    #         record.update_item_line_identifier(entry_no, sequence, blocked)

    #     return res

    
        
    
        
