from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class TmsItemIdentifiers(http.Controller):
    @http.route('/api/tms_item_identifiers', auth='none', methods=['POST'], csrf=False, type='json')
    def create_item_identifiers(self, **kw):
        """
        Create a new Item Identifiers
        """
        data = request.jsonrequest
        code = data.get('Code')
        item_no = data.get('Item_No.')
        variant_code = data.get('Variant_Code')
        unit_of_measure_code = data.get('Unit_of_Measure_Code')
        
        if not code or not item_no:
            return {
                'error': 'Code and Item No. are required',
                'response': 400
            }

        tms_item_identifiers = request.env['tms.item.identifiers'].sudo()

        if tms_item_identifiers.search([('code', '=', code)]):
            uom = tms_item_identifiers.search([('code', '=', code)])
            uom.write({
                'code': code,
                'item_no': item_no,
                'variant_code': variant_code,
                'unit_of_measure_code': unit_of_measure_code
            })
            return {
                'message': 'Item Identifiers updated successfully',
                'response': 200
            }

        try:
            tms_item_identifiers.create({
                'code': code,
                'item_no': item_no,
                'variant_code': variant_code,
                'unit_of_measure_code': unit_of_measure_code
            })
            return {
                'message': 'Item Identifiers created successfully',
                'response': 200
            }
        except Exception as e:
            _logger.error("Error creating Item Identifiers: %s", e)
            return {
                'error': str(e),
                'response': 500
            }
