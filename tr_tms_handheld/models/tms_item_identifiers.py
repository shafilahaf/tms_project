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

    item_no = fields.Many2one('tms.item', string='Item')
    variant_code = fields.Many2one('tms.item.variant', string='Variant Code', domain="[('item_no', '=', item_no)]", store=True)
    unit_of_measure_code = fields.Many2one('tms.unit.of.measures', string='Unit of Measures', store=True)
    barcode_type = fields.Selection([
        ('1', 'GSI 128'),
        ('2','Code 39'),
        ('3', 'QR')
    ], string='Barcode type', required=True)
    barcode_code = fields.Char(string="Barcode Code", store=True)
    entry_no = fields.Integer(string="Entry No")
    item_identifiers_line_ids = fields.One2many('tms.item.identifiers.line', 'header_id', string='Item Identifier Line')
    need_sent_to_wms = fields.Boolean(string="Need Sent to WMS")
    need_sent_to_nav = fields.Boolean(string="Need Sent to NAV")
    from_nav = fields.Boolean(string="From NAV")

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
    
    def create(self):
        if self.from_nav == False:
            self.need_sent_to_nav = True

    def write(self):
        if self.from_nav == False:
            self.need_sent_to_nav = True

    def unlink(self):
        if self.from_nav == False:
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

    def unlink(self):
        if self.from_nav == False:
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
        
    