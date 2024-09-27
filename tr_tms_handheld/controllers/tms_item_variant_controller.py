from odoo import http
from odoo.http import request
import logging
from odoo.addons.project_api.models.common import invalid_response, valid_response
import functools

def validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = request.httprequest.headers.get("access_token")
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)
        access_token_data = request.env["api.access_token"].sudo().search([("token", "=", access_token)],
                                                                          order="id DESC", limit=1)

        if access_token_data.find_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_response("access_token", "token seems to have expired or invalid", 401)

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap

_logger = logging.getLogger(__name__)

class TmsItemVariant(http.Controller):
    @validate_token
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
        tms_item_variant = request.env['tms.item.variant'].sudo()
        
        item = request.env['tms.item'].sudo()
        item_record = item.search([('no', '=', item_no)], limit=1)

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
