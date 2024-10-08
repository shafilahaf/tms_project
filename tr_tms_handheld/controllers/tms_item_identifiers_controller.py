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
    @http.route('/api/tms_item_identifiers', auth='none', methods=['POST'], csrf=False, type='json')
    def create_item_identifiers(self, **kw):
        """
        Create a new Item Identifiers
        """
        data = request.jsonrequest
        item_no = data.get('Item_No')
        variant_code = data.get('Variant_Code')
        unit_of_measure_code = data.get('Unit_of_measure_code')
        barcode_type = data.get('Barcode_Type')
        barcode_code = data.get('Barcode_Code')
        entry_no = data.get('Entry_No')

        tms_item_identifiers = request.env['tms.item.identifiers'].sudo()
        tms_uom_model = request.env['tms.item.uom'].sudo()
        uom = request.env['tms.unit.of.measures'].sudo()
        item = request.env['tms.item'].sudo()

        item_variant = request.env['tms.item.variant'].sudo()

        item_var = item_variant.search([('item_no', '=', item_no), ('code', '=', variant_code)])

        # item_uom = tms_uom_model.search([('code', '=', unit_of_measure_code), ('item_no','=',item_no)], limit=1)
        # if item_uom == False:
        #     return {
        #         'error': "UoM not Found.",
        #         'response': 500,
        #     }
        # else:
        #     uom = uom.search([('code', '=', unit_of_measure_code)])

        uom = False
        item_uom = tms_uom_model.search([('code', '=', unit_of_measure_code), ('item_no','=',item_no)], limit=1)
        if item_uom:
            uom = item_uom.id


        item_record = item.search([('no', '=', item_no)], limit=1)
        if item_record.id == False:
            return {
                'error': "Item not Found.",
                'response': 500,
            }
    
        if tms_item_identifiers.search([('entry_no', '=', entry_no)]):
            item_identifier = tms_item_identifiers.search([('entry_no', '=', entry_no)])
            item_identifier.write({
                'item_no': item_record.id,
                'variant_code': item_var.id if variant_code else False,
                'unit_of_measure_code': uom,#uom.id,
                'barcode_type': barcode_type,
                'sh_product_barcode_mobile':  str(barcode_code),
                'entry_no':int(entry_no),
            })
            return {
                'message': 'Item Identifiers updated successfully',
                'response': 200,
                'Id': item_identifier.id
            }
       
        tms_item_identifiers.create({
            'item_no': item_record.id,
            'variant_code': item_var.id if variant_code else False,
            'unit_of_measure_code': uom,
            'barcode_type': barcode_type,
            'sh_product_barcode_mobile': str(barcode_code),
            'entry_no': int(entry_no),
        })
        item_identifier = tms_item_identifiers.search([('entry_no', '=', entry_no)])
        return {
            'message': 'Item Identifiers created successfully',
            'response': 200,
            'Id': item_identifier.id
        }
      
    
    @validate_token
    @http.route('/api/tms_item_identifiers/<int:id>', auth='none', methods=['DELETE'], csrf=False, type='json')
    def delete_item_identifiers(self, id):
        """
        Create a new Item Identifiers
        """

        tms_item_identifiers = request.env['tms.item.identifiers'].sudo().browse(id)
        if not tms_item_identifiers.exists():
            return {
            'message': 'Item Identifiers Not Found',
            'response': 404,
            }
            #return json.dumps({'status': 'error', 'message': 'Record not found'})

        tms_item_identifiers.from_nav = True
        tms_item_identifiers.sudo().unlink()
        return {
        'message': 'Item Identifiers has been deleted',
        'response': 200,
        }
        #return json.dumps({'status': 'success', 'message': 'Record deleted'})
    
    @validate_token
    @http.route('/api/tms_item_identifier_lines', auth='none', methods=['POST'], csrf=False, type='json')
    def create_item_identifier_lines(self, **kw):
        """
        Create Item Identifier Lines for a specific Item Identifier based on Entry_No.
        """
        data = request.jsonrequest
        entry_no = data.get('Source_Entry_No')

        item_identifier = request.env['tms.item.identifiers'].sudo().search([('entry_no', '=', entry_no)], limit=1)
        line_record = request.env['tms.item.identifiers.line'].sudo()

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

        # line_record = request.env['tms.item.identifiers.line'].sudo().search([
        #     ('header_id', '=', item_identifier.id),
        #     ('header_id.entry_no', '=', entry_no),
        #     ('sequence', '=', sequence)
        # ], limit=1)

        # linerec = request.env['tms.item.identifiers.line'].sudo()

        # if line_record:
        #     line_record.write({
        #         'gs1_identifier': gs1_identifier,
        #         'description': description,
        #         'data_length': data_length,
        #     })
        # else:
        #     iden = linerec.create({ #request.env['tms.item.identifiers.line'].sudo()
        #         'header_id': item_identifier.id,
        #         'sequence': sequence,
        #         'gs1_identifier': gs1_identifier,
        #         'description': description,
        #         'data_length': data_length,
        #     })

        iden = request.env['tms.item.identifiers.line'].sudo()
        iden2 = iden.search([('header_id', '=', item_identifier.id),('header_id.entry_no', '=', entry_no),('sequence', '=', sequence)])

        if iden2:
            iden2.write({
                'gs1_identifier': gs1_identifier,
                'description': description,
                'data_length': data_length,
            })
        else:
            iden2 = iden.create({
                'header_id': item_identifier.id,
                'sequence': sequence,
                'gs1_identifier': gs1_identifier,
                'description': description,
                'data_length': data_length,
            })
            iden2 = iden.search([('header_id', '=', item_identifier.id),('header_id.entry_no', '=', entry_no),('sequence', '=', sequence)])
        return {
            'message': 'Item Identifier Lines processed successfully',
            'response': 200,
            'Id': iden2.id
        }
    
    @validate_token
    @http.route('/api/tms_item_identifier_lines/<int:id>', auth='none', methods=['DELETE'], csrf=False, type='json')
    def delete_item_identifiers_line(self, id):
        """
        Create a new Item Identifiers
        """

        tms_item_identifiers = request.env['tms.item.identifiers.line'].sudo().browse(id)
        if not tms_item_identifiers.exists():
            return {
                'message': 'Item Identifiers Lines Not Found',
                'response': 404,
            }
            #return json.dumps({'status': 'error', 'message': 'Record not found'})

        tms_item_identifiers.from_nav = True
        tms_item_identifiers.sudo().unlink()
        return {
            'message': 'Item Identifiers Lines has Been Deleted',
            'response': 200,
        }
        #return json.dumps({'status': 'success', 'message': 'Record deleted'})