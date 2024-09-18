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
        item_no = data.get('Item_No')
        variant_code = data.get('Variant_Code')
        unit_of_measure_code = data.get('Unit_Of_Measure_Code')
        barcode_type = data.get('Barcode_Type')
        barcode_code = data.get('Barcode_Code')
        blocked = data.get('Blocked')
        entry_no = data.get('Entry_No')

        tms_item_identifiers = request.env['tms.item.identifiers'].sudo()
        tms_uom_model = request.env['tms.unit.of.measures'].sudo()
        item = request.env['tms.item'].sudo()
        
        uom_record = tms_uom_model.search([('code', '=', unit_of_measure_code)], limit=1)
        item_record = item.search([('no', '=', item_no)], limit=1)

        if tms_item_identifiers.search([('item_no', '=', item_no), ('variant_code', '=', variant_code)]):
            item_identifier = tms_item_identifiers.search([('item_no', '=', item_no), ('variant_code', '=', variant_code)])
            item_identifier.write({
                'item_no': item_record.id,
                'variant_code': variant_code,
                'unit_of_measure_code': uom_record.id,
                'barcode_type': barcode_type,
                'barcode_code': barcode_code,
                'blocked': blocked,
                'entry_no': entry_no,
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
                'barcode_code': barcode_code,
                'blocked': blocked,
                'entry_no': entry_no,
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
