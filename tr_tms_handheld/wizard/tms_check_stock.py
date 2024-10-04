from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from requests_ntlm2 import HttpNtlmAuth
import requests
import logging

_logger = logging.getLogger(__name__)
class TMSCheckStockHeader(models.TransientModel):
    _name = 'tms.check.stock.wizard'
    _description = 'TMS Check Stock Wizard'

    sh_product_barcode_mobile = fields.Char(string="Mobile Barcode", store=True)
    item_id = fields.Many2one('tms.item', string='Item No.')
    location_id = fields.Many2one('tms.locations', string='Location')
    check_line_ids = fields.One2many('tms.check.stock.line.wizard', 'wizard_id', string='Check Lines')

    @api.onchange('sh_product_barcode_mobile')
    def _onchange_sh_product_barcode_mobile(self):
        if self.sh_product_barcode_mobile:
            self.parse_gs1_128_barcode(self.sh_product_barcode_mobile)

 
    def parse_gs1_128_barcode(self, barcode):
        barcode_2 = barcode
        if barcode_2[:2] == "01":
            digit_first_14 = barcode_2[2:16] 
        else:
            digit_first_14 = barcode_2

        if digit_first_14:
            item_barcodes = self.env['tms.item.identifiers'].search([
                ('sh_product_barcode_mobile','=', digit_first_14),
            ])
            if item_barcodes:
                self.item_id = item_barcodes.item_no.id


    def check_stock(self):
        current_company = self.env.user.company_id

        if not self.item_id :
             raise ValidationError( f'Item No. must be filled')
        
        self.check_line_ids = [(5, 0, 0)]  # Clear the One2many field

        if self.location_id :
            url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemOdata?$format=json&$filter=No eq \'{self.item_id.no}\' and Location_Filter eq \'{self.location_id.code}\''
        
            self.get_from_nav(url,self.location_id.id)
        else :
            location = self.env['tms.locations'].search([],order = 'priority asc')
            for loc in location :
                url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/ItemOdata?$format=json&$filter=No eq \'{self.item_id.no}\' and Location_Filter eq \'{loc.code}\''
                self.get_from_nav(url,loc.id)
      
    def get_from_nav(self,url,locid) :
        current_company = self.env.user.company_id
        headers = {'Content-Type': 'application/json'}   
        username = current_company.username_api
        password = current_company.password_api
        
        auth = HttpNtlmAuth(username, password)  # Using requests_ntlm2
        
        response = requests.get(url, headers=headers, auth=auth)

        if response.status_code == 400 :
            response_json = response.json()
            resp = response_json.get('odata.error', {}).get('message', {}).get('value', response.text)
            raise ValidationError( f'Nav Error {resp}')
        elif response.status_code == 200 :
            response_json = response.json()

            if 'value' in response_json :
                value = response_json['value'] 
                for data in value :
                    inventory = data['Inventory']
                
                    self.env['tms.check.stock.line.wizard'].create({
                        'location_id': locid,
                        'inventory': inventory,
                        'wizard_id': self.id,
                    })
          
        return False

class TMSCheckStockLine(models.TransientModel):
    _name = 'tms.check.stock.line.wizard'
    _description = 'TMS Check Stock Line Wizard'

    item_id = fields.Many2one('tms.item', string='Item No.')
    location_id = fields.Many2one('tms.locations', string='Location')
    inventory = fields.Float(string="Inventory")
    wizard_id = fields.Many2one('tms.check.stock.wizard', string='Wizard')

    