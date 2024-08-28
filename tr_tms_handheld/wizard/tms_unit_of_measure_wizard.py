from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import requests
import logging
# from requests_ntlm2 import HttpNtlmAuth

_logger = logging.getLogger(__name__)

class TMSUnitofMeasureWizard(models.TransientModel):
    _name = 'tms.unit.of.measure.wizard'
    _description = 'TMS Unit of Measure Wizard'

    description = fields.Char(string='Description', required=True, default='This is wizard for syncing Unit of Measure from NAV')
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)

    
    
    def get_unit_of_measure(self):
        url = f'http://{self.company.ip_or_url_api}:{self.company.port_api}/Thomasong/OData/Company(\'{self.company.name}\')/UOM?$format=json'
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
            tms_uom = self.env['tms.unit.of.measures']
            for uom in data['value']:
                uom_code = tms_uom.search([('code', '=', uom['Code'])])
                if not uom_code:
                    tms_uom.create({
                        'code': uom['Code'],
                        'description': uom['Description'],
                        'etag': uom['ETag']
                    })
                else:
                    uom_code.write({
                        'description': uom['Description'],
                        'etag': uom['ETag']
                    })

                self.update_uom_to_false(uom['Code'], uom['ETag'])
        else:
            raise UserError('No data found in response')
        
        return {
            'name': _('Unit of Measure'),
            'type': 'ir.actions.act_window',
            'res_model': 'tms.unit.of.measures',
            'view_mode': 'tree,form',
            'target': 'current',
        }
    
    def update_uom_to_false(self,code_uom,etag):
        url = f'http://{self.company.ip_or_url_api}:{self.company.port_api}/Thomasong/OData/Company(\'{self.company.name}\')/UOM(\'{code_uom}\')?$format=json'
        headers = {'Content-Type': 'application/json', 'If-Match': f'W/"\'{etag}\'"'}

        username = self.company.username_api
        password = self.company.password_api

        data = {
            "Need_Sent_to_WMS": False
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
    