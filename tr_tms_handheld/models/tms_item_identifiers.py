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
    variant_code = fields.Many2one('tms.item.variant', string='Variant Code', domain="[('item_no', '=', item_no)]", store=True)
    unit_of_measure_code = fields.Many2one('tms.unit.of.measures', string='Unit of Measures', store=True)
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
    need_sent_to_nav = fields.Boolean(string="Need Sent to NAV")

    # SH
    sh_product_barcode_mobile = fields.Char(string="Mobile Barcode", store=True)   
    # SH

    # def unlink_identifier(self):
    #     rec = self.env['tms.item.identifiers'].search([])
    #     rec.unlink()

    @api.onchange('item_no')
    def _onchange_item_no(self):
        # for rec in self:
        if self.item_no:
            item_uom = self.env['tms.item.uom'].search([(
                'item_no','=',self.item_no.no
            )])
            item_uom_array = []
            for itemuom in item_uom:
                item_uom_array.append(itemuom.id)

            return {'domain': {'unit_of_measure_code': [('id', 'in', item_uom_array)]}}
        else:
            return {'domain': {'unit_of_measure_code': []}}

    @api.model
    def create(self, vals):
        if not 'from_nav' in vals:
            self.create_item_identifiers(vals)
        record = super(TmsItemIdentifiers, self).create(vals)
        return record

    def write(self, vals):
        for record in self:
            if not 'from_nav' in vals:
                self.create_item_identifiers(vals)
        vals['need_sent_to_nav'] = True
        res = super(TmsItemIdentifiers, self).write(vals)
        return res
    
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
        
    def create_item_identifiers(self, vals):
       
        # Retrieve etag from response headers
        if self.entry_no == 0:
            self.post_item_identifier(vals)
        else:
            self.update_item_identifier(vals, self.entry_no, blocked=False)

        # vals['need_sent_to_nav'] = True
        
        return False
     
    
    def update_item_identifier(self, vals, entryno, blocked):
        etag = self.retrieve_etag(entryno)
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodes(Entry_No={int(self.entry_no)})?$format=json'
        headers = {'Content-Type': 'application/json', 'If-Match': etag}

        username = current_company.username_api
        password = current_company.password_api

        if 'variant_code' in vals:
            varcode = vals['variant_code'] if vals['variant_code'] else ""
        else:
            varcode = self.variant_code if self.variant_code else ""
        
        if 'sh_product_barcode_mobile' in vals:
            barcode =  vals['sh_product_barcode_mobile']
        else:
            barcode = self.sh_product_barcode_mobile
            
        if 'unit_of_measure_code' in vals:
            uom_code = self.env['tms.unit.of.measures'].search([(
                'id','=', vals['unit_of_measure_code']
            )]).code
        else:
            uom_code = self.unit_of_measure_code.code
            
        if 'barcode_type' in vals:
            bartype = vals['barcode_type']
        else:
            bartype = self.barcode_type
        
       
        data = {
             'Variant_Code': varcode,
             "Barcode_Code":barcode,
             'Unit_Of_Measure_Code': uom_code,
             "Barcode_Type": bartype,
             "Need_Sent_to_WMS": False,
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

    def post_item_identifier(self, vals):
        current_company = self.env.user.company_id
        url2 = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodes?$format=json'
        headers = {'Content-Type': 'application/json'}

        username = current_company.username_api
        password = current_company.password_api
        
        auth = HttpNtlmAuth(username, password)  # Using requests_ntlm2

        blocked = False
        if self.blocked == True:
            blocked = True

       

        uom = self.env['tms.unit.of.measures'].search([(
            'id','=', vals['unit_of_measure_code']
        )])

        item = self.env['tms.item'].search([(
            'id','=', vals['item_no']
        )])

        data2 = {
             'Item_No': item.no,
             'Variant_Code': vals['variant_code'] if vals['variant_code'] else "",
             "Barcode_Code": vals['sh_product_barcode_mobile'],
             'Unit_Of_Measure_Code': uom.code,
             "Barcode_Type": vals['barcode_type'],
             "Need_Sent_to_WMS": False,
        }
        try:
            response = requests.post(url2, headers=headers, auth=auth, json=data2)
            # # response.raise_for_status()

            response_json = response.json()
            entry_no = response_json.get("Entry_No")

            if entry_no:
                vals['entry_no'] = entry_no
            return vals
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

class TMSItemIdentifierLine(models.Model):
    _name = 'tms.item.identifiers.line'
    _description = 'TMS Item Identifiers Line'

    header_id = fields.Many2one('tms.item.identifiers', string='Header', ondelete='cascade')
    sequence = fields.Integer(string="Sequence")
    gs1_identifier = fields.Char(string="GS1 Identifier", size=2)
    description = fields.Char(string="Description", size=50)
    data_length = fields.Integer(string="Data Length")
    need_sent_to_wms = fields.Boolean(string="Need Sent to WMS")
    blocked = fields.Boolean(string="Blocked")
    from_nav = fields.Boolean(string="From NAV", default=False)
    need_sent_to_nav = fields.Boolean(string="Need Sent to NAV", default=True)

    def write(self, vals):
        # Set need_sent_to_nav to True when edited
        if 'need_sent_to_nav' not in vals:
            vals['need_sent_to_nav'] = True
        return super(TMSItemIdentifierLine, self).write(vals)

    def unlink(self):
        self.delete_item_line_identifier(self.retrieve_line_etag(self.header_id.entry_no, self.sequence), self.header_id.entry_no,self.sequence)
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
            
            if response.status_code == 200:
                # Retrieve etag from response headers
                etag = response.headers.get('ETag')
                if not etag:
                    _logger.error("ETag not found in response headers")
                    raise UserError("ETag not found in response headers")
                return etag
            else:
                _logger.error(f"Failed to retrieve ETag for entry_no {entryno} and sequence {sequence}. Status: {response.status_code}, Response: {response.text}")
                raise UserError(f"Failed to retrieve ETag: Status {response.status_code}")

        except requests.exceptions.RequestException as e:
            _logger.error(f"HTTP error occurred: {e}")
            raise UserError(f"HTTP error occurred: {e}")
        except ValueError as e:
            _logger.error(f"JSON decode error: {e}")
            _logger.error(f"Response content: {response.text}")
            raise UserError(f"JSON decode error: {e}")

    # scheduler
    def post_patch_item_identifiers_to_api(self):
        # Get all records that need to be sent to WMS
        # lines_to_post = self.search([('header_id.need_sent_to_nav', '=', True)])
        lines_to_post = self.search([('need_sent_to_nav', '=', True)])

        current_company = self.env.user.company_id
        base_url = f"http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company('{current_company.name}')/ItemBarcodesDetail"
        headers = {'Content-Type': 'application/json'}
        username = current_company.username_api
        password = current_company.password_api
        auth = HttpNtlmAuth(username, password)

        for line in lines_to_post:
            if line.header_id and line.header_id.entry_no:
                entry_no = line.header_id.entry_no

                payload = {
                    "Source_Entry_No": entry_no,
                    "Sequence": line.sequence,
                    "GS1_Identifier": line.gs1_identifier,
                    "Description": line.description,
                    "Data_Length": line.data_length
                }
                check_url = f"{base_url}?$filter=Source_Entry_No eq {entry_no} and Sequence eq {line.sequence}&$format=json"

                try:
                    get_response = requests.get(check_url, headers=headers, auth=auth)
                    
                    if get_response.status_code == 200:
                        data = get_response.json()

                        if data and data['value']:
                            patch_url = f"{base_url}(Source_Entry_No={entry_no},Sequence={line.sequence})?$format=json"
                            etag = self.retrieve_line_etag(entry_no, line.sequence)
                            patch_headers = {
                                'Content-Type': 'application/json',
                                'If-Match': etag
                            }
                            patch_response = requests.patch(patch_url, headers=patch_headers, auth=auth, json=payload)

                            if patch_response.status_code == 204:
                                line.header_id.need_sent_to_nav = False
                                line.need_sent_to_nav = False
                                _logger.info(f"Successfully updated record {line.id} in NAV.")
                            else:
                                _logger.error(f"Failed to update line {line.id}. Status: {patch_response.status_code}, Response: {patch_response.text}")

                        # If no record is found, create a new one with POST request
                        else:
                            post_response = requests.post(base_url, headers=headers, auth=auth, json=payload)
                            if post_response.status_code == 201:
                                line.header_id.need_sent_to_nav = False
                                line.need_sent_to_nav = False
                                _logger.info(f"Successfully created record {line.id} in NAV.")
                            else:
                                _logger.error(f"Failed to create line {line.id}. Status: {post_response.status_code}, Response: {post_response.text}")
                    
                    else:
                        _logger.error(f"Failed to check existing records for line {line.id}. Status: {get_response.status_code}, Response: {get_response.text}")

                except requests.exceptions.RequestException as e:
                    _logger.error(f"Error sending line {line.id} to NAV: {str(e)}")
    # scheduler



    
        
    
        
