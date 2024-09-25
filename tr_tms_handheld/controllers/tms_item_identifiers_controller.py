from odoo import http
from odoo.http import request
import logging
import json

from odoo.addons.project_api.models.common import invalid_response, valid_response
import functools

_logger = logging.getLogger(__name__)

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

class TmsItemIdentifiers(http.Controller):
    @validate_token
    @http.route('/api/tms_item_identifiers', auth='none', methods=['GET'], csrf=False, type='http')
    def get_item_identifier(self,**kw):
        # data = request.jsonrequest
        # tms_item_identifiers = request.env['tms.item.identifiers'].sudo()
        # item_identifier = request.env['tms.item.identifiers'].sudo().search([('header_id', '=', tms_item_identifiers.id)], limit=1)

        items = request.env['tms.item.identifiers'].sudo().search([(
            'need_sent_to_nav', '=', True
        )])
        items_data = []
        for item in items:
            items_data.append({
                'id': item.id,
                'item_no': item.item_no.no,
                'variant_code': item.variant_code.code,
                'unit_of_measure_code': item.unit_of_measure_code.code,
                'barcode_type': item.barcode_type,
                'sh_product_barcode_mobile': item.sh_product_barcode_mobile

            })
        return json.dumps({'status': 'success', 'data': items_data})
    
    @validate_token
    @http.route('/api/tms_item_identifier_lines', auth='none', methods=['GET'], csrf=False, type='http')
    def get_item_line_identifier(self,**kw):
        # data = request.jsonrequest
        # tms_item_identifiers = request.env['tms.item.identifiers'].sudo()
        # item_identifier = request.env['tms.item.identifiers'].sudo().search([('header_id', '=', tms_item_identifiers.id)], limit=1)

        items = request.env['tms.item.identifiers.line'].sudo().search([(
            'need_sent_to_nav', '=', True
        )])
        items_data = []
        for item in items:
            items_data.append({
                'id': item.id,
                'entry_no': item.header_id.entry_no,
                'sequence': item.sequence,
                'gs1_identifier': item.gs1_identifier,
                'description': item.description,
                'data_length': item.data_length,
            })
        return json.dumps({'status': 'success', 'data': items_data})

    @validate_token
    @http.route('/api/tms_item_identifiers', auth='none', methods=['POST'], csrf=False, type='json')
    def create_item_identifiers(self, **kw):
        """
        Create a new Item Identifiers
        """
        data = request.jsonrequest
        item_no = data.get('Item_No')
        variant_code = data.get('Variant_Code')
        unit_of_measure_code = data.get('Unit_Of_Measure_Code')
        barcode_type = data.get('Barcode_Type')
        barcode_code = data.get('Barcode_Code')
        entry_no = data.get('Entry_No')

        tms_item_identifiers = request.env['tms.item.identifiers'].sudo()
        tms_uom_model = request.env['tms.unit.of.measures'].sudo()
        item = request.env['tms.item'].sudo()

        uom_record = tms_uom_model.search([('code', '=', unit_of_measure_code)], limit=1)
        item_record = item.search([('no', '=', item_no)], limit=1)

        if tms_item_identifiers.search([('entry_no', '=', entry_no)]):
            item_identifier = tms_item_identifiers.search([('entry_no', '=', entry_no)])
            item_identifier.write({
                'item_no': item_record.id,
                'variant_code': variant_code,
                'unit_of_measure_code': uom_record.id,
                'barcode_type': barcode_type,
                'sh_product_barcode_mobile': barcode_code,
                'entry_no': entry_no,
                'need_sent_to_nav': False,
            })
            return {
                'message': 'Item Identifiers updated successfully',
                'response': 200
            }
        try:
            tms_item_identifiers.create({
                'item_no': item_record.id,
                'variant_code': variant_code,
                'unit_of_measure_code': uom_record.id,
                'barcode_type': barcode_type,
                'sh_product_barcode_mobile': barcode_code,
                'entry_no': entry_no,
                'need_sent_to_nav': False,
            })
            return {
                'message': 'Item Identifiers created successfully',
                'response': 200
            }
        except Exception as e:
            _logger.error("Error fetching Item Journal Line: %s", e)
            return {
                'error': str(e),
                'response': 500
            }
    
    @validate_token
    @http.route('/api/tms_item_identifiers/<int:id>', auth='none', methods=['DELETE'], csrf=False, type='http')
    def delete_item_identifiers(self, id):
        """
        Create a new Item Identifiers
        """

        tms_item_identifiers = request.env['tms.item.identifiers'].sudo().browse(id)
        if not tms_item_identifiers.exists():
            return json.dumps({'status': 'error', 'message': 'Record not found'})

        tms_item_identifiers.from_nav = True
        tms_item_identifiers.sudo().unlink()
        return json.dumps({'status': 'success', 'message': 'Record deleted'})
    
    @validate_token
    @http.route('/api/tms_item_identifier_lines', auth='none', methods=['POST'], csrf=False, type='json')
    def create_item_identifier_lines(self, **kw):
        """
        Create Item Identifier Lines for a specific Item Identifier based on Entry_No.
        """
        data = request.jsonrequest
        entry_no = data.get('Source_Entry_No')

        item_identifier = request.env['tms.item.identifiers'].sudo().search([('entry_no', '=', entry_no)], limit=1)

        if not item_identifier.exists():
            return {
                'error': 'Item Identifier not found for the given Entry No',
                'response': 404
            }

        # for line in item_identifier_lines:
        sequence = data.get('Sequence')
        entry_no = data.get('Source_Entry_No')
        gs1_identifier = data.get('GS1_Identifier')
        description = data.get('Description')
        data_length = data.get('Data_Length')

        line_record = request.env['tms.item.identifiers.line'].sudo().search([
            ('header_id', '=', item_identifier.id),
            ('header_id.entry_no', '=', entry_no),
            ('sequence', '=', sequence)
        ], limit=1)

        if line_record:
            line_record.write({
                'gs1_identifier': gs1_identifier,
                'description': description,
                'data_length': data_length,
            })
        else:
            request.env['tms.item.identifiers.line'].sudo().create({
                'header_id': item_identifier.id,
                'sequence': sequence,
                'gs1_identifier': gs1_identifier,
                'description': description,
                'data_length': data_length,
            })

        return {
            'message': 'Item Identifier Lines processed successfully',
            'response': 200
        }
    
    @validate_token
    @http.route('/api/tms_item_identifier_lines/<int:id>', auth='none', methods=['DELETE'], csrf=False, type='http')
    def delete_item_identifiers_line(self, id):
        """
        Create a new Item Identifiers
        """

        tms_item_identifiers = request.env['tms.item.identifiers.line'].sudo().browse(id)
        if not tms_item_identifiers.exists():
            return json.dumps({'status': 'error', 'message': 'Record not found'})

        tms_item_identifiers.from_nav = True
        tms_item_identifiers.sudo().unlink()
        return json.dumps({'status': 'success', 'message': 'Record deleted'})