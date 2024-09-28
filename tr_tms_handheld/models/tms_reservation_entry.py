from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging
import requests
from requests_ntlm2 import HttpNtlmAuth

class TMSReservationEntry(models.Model):
    _name = 'tms.reservation.entry'
    _description = 'TMS Reservation Entry'
    
    item_no = fields.Char('Item No')
    location_code = fields.Char('Location Code')
    source_type = fields.Selection([
        ('39', 'Purchase Order'),
        ('37', 'Sales Order'),
        ('5741', 'Transfer Order'),
        ('83', 'Item Journal')
    ], string="Source Type")
    source_id = fields.Char('Source Id') # Doc No.
    source_ref_no = fields.Integer('Source Ref.') # Line No.
    quantity = fields.Float('Quantity')
    expiration_date = fields.Date('Expiration Date')
    serial_no = fields.Char('Serial No.')
    lot_no = fields.Char('Lot No.')
    source_type_int = fields.Integer('Source Type Int', compute='_compute_source_type_int', store=True)
    
    purchase_scan_id = fields.Many2one('tms.handheld.transaction.scan', string='purchase_scan_id')
  
    ##
    line_id = fields.Integer('Line_ID')
    line_no = fields.Integer('Line No')
    
    @api.depends('source_type')
    def _compute_source_type_int(self):
        for record in self:
            # Map selection values to integer values
            source_type_map = {
                '39': 39,   # Purchase Order
                '37': 37,   # Sales Order
                '5741': 5741, # Transfer Order
                '83': 83    # Item Journal
            }
            record.source_type_int = source_type_map.get(record.source_type, 0)
    
    def unlink(self):
        """
        Override the unlink method to update qty_to_receive in tms.handheld.transaction.line 
        when a reservation entry is deleted.
        """
        for entry in self:

            purchase_receipt_header = self.env['tms.handheld.transaction'].search([
                ('document_no', '=', entry.source_id)
            ], limit=1)

            # Prevent delete when purchase receipt submit
            if purchase_receipt_header and purchase_receipt_header.state in ['submitted']:
                raise ValidationError("You cannot delete a reservation entry when the related purchase receipt is posted or submitted.")
            

            purchase_receipt_line = self.env['tms.handheld.transaction.line'].search([
                ('item_no.no', '=', entry.item_no),
                ('handheld_transaction_id.document_no', '=', entry.source_id)
            ], limit=1)

            if purchase_receipt_line:
                remaining_reservation_entries = self.env['tms.reservation.entry'].search([
                    ('item_no', '=', entry.item_no),
                    ('source_id', '=', entry.source_id),
                    ('id', '!=', entry.id)  
                ])

                if remaining_reservation_entries:
                    purchase_receipt_line.qty_to_receive = sum(remaining_reservation_entries.mapped('quantity'))
                    abcd = sum(remaining_reservation_entries.mapped('quantity'))
                    print(abcd)
                else:
                    purchase_receipt_line.qty_to_receive = 0.0

            if entry.source_id :
                etag = self.retrieve_etag(purchase_receipt_line.handheld_transaction_id.id)
                if etag:
                    self.fnDeleteSNInformationonNav(etag, purchase_receipt_line.handheld_transaction_id.id)
        return super(TMSReservationEntry, self).unlink()
    
    def retrieve_etag(self,headerid):
        current_company = self.env.user.company_id

        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/Handheld_SN_OData(Processed_Header_ID={headerid},Line_ID={self.line_id},Line_No={self.line_no},Serial_No=\'{self.serial_no if self.serial_no else ""}\',Lot_No=\'{self.lot_no if self.lot_no else ""}\')?$format=json'

        headers = {'Content-Type': 'application/json'}
        
        username = current_company.username_api
        password = current_company.password_api
        
        if username == False or password == False or  current_company.ip_or_url_api == False or current_company.port_api == False:
             raise ValidationError( f'You have to setup API Connection in companies')
        
        auth = HttpNtlmAuth(username, password)
        response = requests.get(url, headers=headers, auth=auth)
       
        if response.status_code == 400 :
            response_json = response.json()
            resp = response_json.get('odata.error', {}).get('message', {}).get('value', response.text)
            raise ValidationError( f'Nav Error {resp}')

        # Retrieve etag from response headers
        etag = response.headers.get('ETag')
        if not etag:
            raise UserError("ETag not found in response headers")

        return etag
    
    def fnDeleteSNInformationonNav(self, etag,headerid):
        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/Handheld_SN_OData(Processed_Header_ID={headerid},Line_ID={self.line_id},Line_No={self.line_no},Serial_No=\'{self.serial_no if self.serial_no else ""}\',Lot_No=\'{self.lot_no if self.lot_no else ""}\')?$format=json'
        headers = {'Content-Type': 'application/json', 'If-Match': etag}

        username = current_company.username_api
        password = current_company.password_api

        if username == False or password == False or  current_company.ip_or_url_api == False or current_company.port_api == False:
             raise ValidationError( f'You have to setup API Connection in companies')
        
        auth = HttpNtlmAuth(username, password)
        response = requests.delete(url, headers=headers, auth=auth)
       
        if response.status_code == 400:
            response_json = response.json()
            resp = response_json.get('odata.error', {}).get('message', {}).get('value', response.text)
            raise ValidationError( f'Nav Error {resp}')