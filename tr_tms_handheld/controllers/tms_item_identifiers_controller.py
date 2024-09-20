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

    @http.route('/api/tms_item_identifier_lines', auth='none', methods=['POST'], csrf=False, type='json')
    def create_item_identifier_lines(self, **kw):
        """
        Create Item Identifier Lines for a specific Item Identifier based on Entry_No.
        """
        data = request.jsonrequest
        entry_no = data.get('Entry_No')
        item_identifier_lines = data.get('Item_Identifier_Lines')

        if not item_identifier_lines or not entry_no:
            return {
                'error': 'Entry No and lines are required',
                'response': 400
            }

        # Find the Item Identifier by Entry_No
        item_identifier = request.env['tms.item.identifiers'].sudo().search([('entry_no', '=', entry_no)], limit=1)

        if not item_identifier.exists():
            return {
                'error': 'Item Identifier not found for the given Entry No',
                'response': 404
            }

        for line in item_identifier_lines:
            sequence = line.get('Sequence')
            gs1_identifier = line.get('GS1_Identifier')
            description = line.get('Description')
            data_length = line.get('Data_Length')

            # Check if the line with the given sequence already exists
            line_record = request.env['tms.item.identifiers.line'].sudo().search([
                ('header_id', '=', item_identifier.id),
                ('sequence', '=', sequence)
            ], limit=1)

            if line_record:
                # Update existing line
                line_record.write({
                    'gs1_identifier': gs1_identifier,
                    'description': description,
                    'data_length': data_length
                })
            else:
                # Create new line if it doesn't exist
                request.env['tms.item.identifiers.line'].sudo().create({
                    'header_id': item_identifier.id,
                    'sequence': sequence,
                    'gs1_identifier': gs1_identifier,
                    'description': description,
                    'data_length': data_length
                })

        return {
            'message': 'Item Identifier Lines processed successfully',
            'response': 200
        }