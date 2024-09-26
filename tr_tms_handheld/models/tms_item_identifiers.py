from odoo import models, fields, api, _
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

    item_no = fields.Many2one('tms.item', string='Item', store=True)
    variant_code = fields.Many2one('tms.item.variant', string='Variant Code', domain="[('item_no', '=', item_no)]", store=True)
    unit_of_measure_code = fields.Many2one('tms.unit.of.measures', string='Unit of Measures', store=True, required=True)
    barcode_type = fields.Selection([
        ('1', 'GSI 128'),
        ('2','EAN'),
        ('3', 'QR')
    ], string='Barcode type', required=True)
    barcode_code = fields.Char(string="Barcode Code", store=True, required=True)
    entry_no = fields.Integer(string="Entry No")
    item_identifiers_line_ids = fields.One2many('tms.item.identifiers.line', 'header_id', string='Item Identifier Line')
    need_sent_to_wms = fields.Boolean(string="Need Sent to WMS")
    from_nav = fields.Boolean(string="From NAV")

    sh_product_barcode_mobile = fields.Char(string="Mobile Barcode", store=True)


    def create_identifier_line(self):
        return {
            'name': 'Item Line Identifiers',
            'type': 'ir.actions.act_window',
            'res_model': 'tms.item.identifiers.line',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_source_entry_no': self.entry_no,
                'create': True, 'edit': True, 'delete': True,
                'from_odoo': True,
                'default_header_id': self.id,
            },
            'domain': [('source_entry_no', '=', self.entry_no)]
        }

    @api.onchange('item_no')
    def _onchange_item_no(self):
        # for rec in self:
        if self.item_no:
            item_uom = self.env['tms.item.uom'].search([(
                'item_no','=',self.item_no.no
            )])
            item_uom_array = []
            for itemuom in item_uom:
                item_uom_array.append(itemuom.code)

            return {'domain': {'unit_of_measure_code': [('code', 'in', item_uom_array)]}}
        else:
            return {'domain': {'unit_of_measure_code': []}}
        
    @api.model
    def create(self, vals):
        record = super(TmsItemIdentifiers, self).create(vals)
        if self._context.get('from_odoo'):
            self.create_item_identifiers(vals, record)

        return record


    def write(self, vals):
        res = super(TmsItemIdentifiers, self).write(vals)
        for record in self:
            if self._context.get('from_odoo'):
                self.create_item_identifiers(vals, record)

        return res
    
    def unlink(self):
        for record in self:
            if self._context.get('from_odoo'):
                etag = self.retrieve_etag(self.item_no.no,self.entry_no)
                if etag:
                    self.delete_item_identifier(etag, self.entry_no)
        # Proceed with the standard unlink process
        return super(TmsItemIdentifiers, self).unlink()

    # SENd API to NAV
    def retrieve_etag(self, itemno ,entryno):
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodes(Item_No=\'{itemno}\',Entry_No={int(self.entry_no)})?$format=json'
        
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
                # raise UserError("ETag not found in response headers")

            return etag

        except requests.exceptions.RequestException as e:
            _logger.error(f"HTTP error occurred: {e}")
            raise UserError(f"HTTP error occurred: {e}")
        except ValueError as e:
            _logger.error(f"JSON decode error: {e}")
            _logger.error(f"Response content: {response.text}")
            raise UserError(f"JSON decode error: {e}")
        

    def create_item_identifiers(self, vals, rec):
       
        # Retrieve etag from response headers
        if self.entry_no == 0:
            self.post_item_identifier(vals, rec)
        else:
            self.update_item_identifier(vals, self.entry_no, rec)

    def update_item_identifier(self, vals, entryno, rec):
        etag = self.retrieve_etag(self.item_no.no,entryno)
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodes(Item_No=\'{self.item_no.no}\',Entry_No={int(self.entry_no)})?$format=json'
        headers = {'Content-Type': 'application/json', 'If-Match': etag}

        username = current_company.username_api
        password = current_company.password_api

        if 'variant_code' in vals:
            varcode = ''
            varcode2 = vals['variant_code'] if vals['variant_code'] else ""
            if varcode2:
                variant = self.env['tms.item.variant'].search([
                    ('id','=', varcode2)
                ])
                if variant:
                    varcode = variant.code
        else:
            varcode = self.variant_code.code if self.variant_code.code else ""
        
        if 'sh_product_barcode_mobile' in vals:
            barcode =  vals['sh_product_barcode_mobile']
        else:
            barcode = self.sh_product_barcode_mobile

        if barcode:
            existing_barcode = self.env['tms.item.identifiers'].search([
                ('sh_product_barcode_mobile', '=', barcode),
                ('id', '!=', self.id)
            ], limit=1)
            
            if existing_barcode:
                raise UserError(f"The barcode {barcode} is already assigned to another item.")
            
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
             "Id": rec.id,
        }

        try:
            auth = HttpNtlmAuth(username, password)
            response = requests.patch(url, headers=headers, auth=auth, json=data)

            if response.status_code == 400:
                response_json = response.json()
                resp = response_json.get('odata.error', {}).get('message', {}).get('value', response.text)
                raise ValidationError(resp)


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

    def post_item_identifier(self, vals, rec):
        current_company = self.env.user.company_id
        url2 = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodes?$format=json'
        headers = {'Content-Type': 'application/json'}

        username = current_company.username_api
        password = current_company.password_api
        
        auth = HttpNtlmAuth(username, password)  # Using requests_ntlm2


        if 'item_no' in vals:
            item_no = vals['item_no'] if vals['item_no'] else ""
        else:
            item_no = self.item_no if self.item_no else ""
        
        if 'variant_code' in vals:
            varcode = ''
            varcode2 = vals['variant_code'] if vals['variant_code'] else ""
            if varcode2:
                variant = self.env['tms.item.variant'].search([
                    ('id','=', varcode2)
                ])
                if variant:
                    varcode = variant.code
        else:
            varcode = self.variant_code.code if self.variant_code.code else ""
        
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


        uom = self.env['tms.unit.of.measures'].search([(
            'id','=', self.unit_of_measure_code.id
        )])

        item = self.env['tms.item'].search([(
            'id','=', item_no
        )])

        data2 = {
             'Item_No': item.no,
             'Variant_Code': varcode,
             "Barcode_Code":barcode,
             'Unit_Of_Measure_Code': uom_code,
             "Barcode_Type": bartype,
             "Need_Sent_to_WMS": False,
             "Id": rec.id,
        }
        try:
            response = requests.post(url2, headers=headers, auth=auth, json=data2)
            # # response.raise_for_status()

            response_json = response.json()
            entry_no = response_json.get("Entry_No")

            if entry_no:
                rec.entry_no = entry_no
                self.entry_no = entry_no
            else :
                resp = response_json.get('odata.error', {}).get('message', {}).get('value', response.text)
                raise ValidationError(resp)

            # return vals
        except requests.exceptions.HTTPError as e:
            try:
                root = ET.fromstring(response.text)
                error_message = root.find('.//m:message', {'m': 'http://schemas.microsoft.com/ado/2007/08/dataservices/metadata'}).text
            except ET.ParseError:
                error_message = response.text  # Fallback to the full response text if XML parsing fails
            _logger.error(f"HTTP error occurred while create item idenfirers: {error_message}")
            raise UserError(error_message)
    
    def delete_item_identifier(self, etag, entryno):
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodes(Item_No=\'{self.item_no.no}\',Entry_No={int(entryno)})?$format=json'
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
    # SENd API to NAV


class TMSItemIdentifierLine(models.Model):
    _name = 'tms.item.identifiers.line'
    _description = 'TMS Item Identifiers Line'

    header_id = fields.Many2one('tms.item.identifiers', string='Header', ondelete='cascade')
    sequence = fields.Integer(string="Sequence")
    gs1_identifier = fields.Char(string="GS1 Identifier", size=2)
    description = fields.Char(string="Description", size=50)
    data_length = fields.Integer(string="Data Length")
    need_sent_to_wms = fields.Boolean(string="Need Sent to WMS")
    need_sent_to_nav = fields.Boolean(string="Need Sent to NAV", default=True)
    from_nav = fields.Boolean(string="From NAV")
    source_entry_no = fields.Integer(string="Source Entry No.")

    @api.constrains('sequence', 'header_id')
    def _check_unique_sequence(self):
        """ Ensure the sequence is unique per header_id """
        for record in self:
            if record.sequence:
                duplicate = self.search([
                    ('sequence', '=', record.sequence),
                    ('header_id', '=', record.header_id.id),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    raise ValidationError(f"Sequence {record.sequence} already exists for this header.")
            if record.sequence == 0:
                raise ValidationError(_("Sequence cannot be 0. Please assign a valid sequence number."))

     # Line
    @api.model
    def create(self, vals):
        record = super(TMSItemIdentifierLine, self).create(vals)
        if self._context.get('from_odoo'):
            self.create_item_identifiers_line(vals, record)
        
        return record

   
    def write(self, vals):
        res = super(TMSItemIdentifierLine, self).write(vals)
        for record in self:
            if self._context.get('from_odoo'):
                self.create_item_identifiers_line(vals, record)
        return res
    
    def unlink(self):
        if self._context.get('from_odoo'):
            etag = self.retrieve_line_etag(self.header_id.entry_no, self.sequence)
            if etag:
                self.delete_item_line_identifier(etag, self.header_id.entry_no,self.sequence)
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

        
    def create_item_identifiers_line(self, vals, rec):
       
        
        # Retrieve etag from response headers
        if self.id == False:
            self.post_item_identifier_line(vals, rec)
        else:
            self.update_item_identifier_line(vals, rec)

    
    def update_item_identifier_line(self, vals, rec):
      
        
        header = self.env['tms.item.identifiers'].search([
            ('item_identifiers_line_ids', '=', rec.header_id.id)])
       
        if 'sequence' in vals:
            sequence = vals['sequence'] if vals['sequence'] else ""
        else:
            sequence = self.sequence if self.sequence else ""
        
        if 'gs1_identifier' in vals:
            gs1_identifier = vals['gs1_identifier'] if vals['gs1_identifier'] else ""
        else:
            gs1_identifier = self.gs1_identifier if self.gs1_identifier else ""
        
        if 'description' in vals:
            description =  vals['description']
        else:
            description = self.description
            
        if 'data_length' in vals:
            data_length =  vals['data_length']
        else:
            data_length = self.data_length

        etag = self.retrieve_line_etag(rec.header_id.entry_no, rec.sequence)
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodesDetail(Source_Entry_No={int(rec.header_id.entry_no)},Sequence={rec.sequence})?$format=json'
        headers = {'Content-Type': 'application/json', 'If-Match': etag}

        username = current_company.username_api
        password = current_company.password_api

        data = {
             "GS1_Identifier":gs1_identifier,
             'Description': description,
             "Data_Length": data_length,
             "Need_Sent_to_WMS": False,
             "Id": rec.id,
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

    def post_item_identifier_line(self, vals, rec):
        current_company = self.env.user.company_id
        url2 = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemBarcodesDetail?$format=json'
        headers = {'Content-Type': 'application/json'}

        username = current_company.username_api
        password = current_company.password_api
        
        auth = HttpNtlmAuth(username, password)  # Using requests_ntlm2


        if 'sequence' in vals:
            sequence = vals['sequence'] if vals['sequence'] else ""
        else:
            sequence = self.sequence if self.sequence else ""
        
        if 'gs1_identifier' in vals:
            gs1_identifier = vals['gs1_identifier'] if vals['gs1_identifier'] else ""
        else:
            gs1_identifier = self.gs1_identifier if self.gs1_identifier else ""
        
        if 'description' in vals:
            description =  vals['description']
        else:
            description = self.description
            
        if 'data_length' in vals:
            data_length =  vals['data_length']
        else:
            data_length = self.data_length

        header = self.env['tms.item.identifiers'].search([
            ('id', '=', rec.header_id.id)
        ])
        
        data2 = {
             'Source_Entry_No': header.entry_no,
             'Sequence': sequence,
             "GS1_Identifier":gs1_identifier,
             'Description': description,
             "Data_Length": data_length,
             "Need_Sent_to_WMS": False,
             "Id": rec.id
        }
        try:
            response = requests.post(url2, headers=headers, auth=auth, json=data2)
            # # response.raise_for_status()

            response_json = response.json()
        except requests.exceptions.HTTPError as e:
            try:
                root = ET.fromstring(response.text)
                error_message = root.find('.//m:message', {'m': 'http://schemas.microsoft.com/ado/2007/08/dataservices/metadata'}).text
            except ET.ParseError:
                error_message = response.text  # Fallback to the full response text if XML parsing fails
            _logger.error(f"HTTP error occurred while create item idenfirers: {error_message}")
            raise UserError(error_message)