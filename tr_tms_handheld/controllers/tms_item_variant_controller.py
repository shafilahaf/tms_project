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
        # barcode_type_id = data.get('Barcode_Type')
        # barcode_code = data.get('Barcode_Code')

        tms_item_variant = request.env['tms.item.variant'].sudo()
        
        item = request.env['tms.item'].sudo()
        item_record = item.search([('no', '=', item_no)], limit=1)
        
        # barcode_record = None
        # if barcode_type_id:
        #     # Search for the barcode type, if not found create a new one
        #     barcode = request.env['tms.barcode.type'].sudo()
        #     barcode_record = barcode.search([('name', '=', barcode_type_id)], limit=1)
        #     if not barcode_record:
        #         barcode_record = barcode.create({
        #             'name': barcode_type_id
        #         })

        if tms_item_variant.search([('code', '=', code)]):
            uom = tms_item_variant.search([('code', '=', code)])
            uom.write({
                'code': code,
                'item_no': item_record.id,
                'description': description,
                'description_2': description_2,
                # 'barcode_type_id': barcode_record.id if barcode_record else False,
                # 'barcode_code': barcode_code if barcode_record else False
                
            })
            return {
                'message': 'Item Variant updated successfully',
                'response': 200
            }

        try:
            tms_item_variant.create({
                'code': code,
                'item_no': item_record.id,
                'description': description,
                'description_2': description_2,
                # 'barcode_type_id': barcode_record.id if barcode_record else False,
                # 'barcode_code': barcode_code if barcode_record else False
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
