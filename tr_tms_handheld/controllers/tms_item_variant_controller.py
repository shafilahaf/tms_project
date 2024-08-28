from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class TmsItemVariant(http.Controller):
    @http.route('/api/tms_item_variant', auth='none', methods=['POST'], csrf=False, type='json')
    def create_item_variant(self, **kw):
        """
        Create a new Item Variant
        """
        data = request.jsonrequest
        code = data.get('Code')
        item_no = data.get('Item_No.')
        description = data.get('Description')
        description_2 = data.get('Description_2')
        
        if not code or not item_no:
            return {
                'error': 'Code and Item No. are required',
                'response': 400
            }

        tms_item_variant = request.env['tms.item.variant'].sudo()

        if tms_item_variant.search([('code', '=', code)]):
            uom = tms_item_variant.search([('code', '=', code)])
            uom.write({
                'code': code,
                'item_no': item_no,
                'description': description,
                'description_2': description_2
            })
            return {
                'message': 'Item Variant updated successfully',
                'response': 200
            }

        try:
            tms_item_variant.create({
                'code': code,
                'item_no': item_no,
                'description': description,
                'description_2': description_2
            })
            return {
                'message': 'Item Variant created successfully',
                'response': 200
            }
        except Exception as e:
            _logger.error("Error creating Item Variant: %s", e)
            return {
                'error': str(e),
                'response': 500
            }
