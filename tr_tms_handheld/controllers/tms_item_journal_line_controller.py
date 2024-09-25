from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class TMSItemJournalLine(http.Controller):
    
    @http.route('/api/tms_item_journal_line', auth='public', methods=['POST'], csrf=False, type='json')
    def create_item_journal_line(self, **kw):
        try:
            data = request.jsonrequest
            line_no = data.get('Line No.')
            item_no = data.get('Item No')
            posting_date = data.get('Posting Date')
            entry_type = data.get('Entry Type')
            document_no = data.get('Document No')
            description = data.get('Description')
            location_code = data.get('Location Code')
            quantity = data.get('Quantity')
            journal_batch_name = data.get('Journal Batch Name')
            qty_calculated = data.get('Qty. (Calculated)')
            qty_phys_inventory = data.get('Qty. (Phys. Inventory)')
            phys_inventory = data.get('Phys. Inventory')
            external_document_no = data.get('External Document No.')
            variant_code = data.get('Variant Code')
            qty_per_unit_measure = data.get('Qty. per Unit of Measure')
            unit_of_measure_code = data.get('Unit of Measure Code')
            quantity_base = data.get('Quantity (Base)')

            # Create new item journal line
            item_journal_line = request.env['tms.item.journal.line'].create({
                'line_no': line_no,
                'item_no': item_no,
                'posting_date': posting_date,
                'entry_type': entry_type,
                'document_no': document_no,
                'description': description,
                'location_code': location_code,
                'quantity': quantity,
                'journal_batch_name': journal_batch_name,
                'qty_calculated': qty_calculated,
                'qty_phys_inventory': qty_phys_inventory,
                'phys_inventory': phys_inventory,
                'external_document_no': external_document_no,
                'variant_code': variant_code,
                'qty_per_unit_measure': qty_per_unit_measure,
                'unit_of_measure_code': unit_of_measure_code,
                'quantity_base': quantity_base
            })

            return {
                'message': 'Item Journal Line created successfully',
                'id': item_journal_line.id,
                'response': 200
            }
        except Exception as e:
            _logger.error("Error creating Item Journal Line: %s", e)
            return {
                'error': str(e),
                'response': 500
            }

    @http.route('/api/tms_item_journal_line/<int:id>', auth='public', methods=['GET'], csrf=False, type='json')
    def get_item_journal_line(self, id, **kw):
        try:
            item_journal_line = request.env['tms.item.journal.line'].sudo().browse(id)
            if item_journal_line.exists():
                return {
                    'line_no': item_journal_line.line_no,
                    'item_no': item_journal_line.item_no,
                    'posting_date': item_journal_line.posting_date,
                    'entry_type': item_journal_line.entry_type,
                    'document_no': item_journal_line.document_no,
                    'description': item_journal_line.description,
                    'location_code': item_journal_line.location_code,
                    'quantity': item_journal_line.quantity,
                    'journal_batch_name': item_journal_line.journal_batch_name,
                    'qty_calculated': item_journal_line.qty_calculated,
                    'qty_phys_inventory': item_journal_line.qty_phys_inventory,
                    'phys_inventory': item_journal_line.phys_inventory,
                    'external_document_no': item_journal_line.external_document_no,
                    'variant_code': item_journal_line.variant_code,
                    'qty_per_unit_measure': item_journal_line.qty_per_unit_measure,
                    'unit_of_measure_code': item_journal_line.unit_of_measure_code,
                    'quantity_base': item_journal_line.quantity_base,
                }
            else:
                return {
                    'message': 'Item Journal Line not found',
                    'response': 404
                }
        except Exception as e:
            _logger.error("Error fetching Item Journal Line: %s", e)
            return {
                'error': str(e),
                'response': 500
            }

    @http.route('/api/tms_item_journal_line/<int:id>', auth='public', methods=['PUT'], csrf=False, type='json')
    def update_item_journal_line(self, id, **kw):
        try:
            data = request.jsonrequest
            item_journal_line = request.env['tms.item.journal.line'].sudo().browse(id)
            if item_journal_line.exists():
                item_journal_line.write({
                    'line_no': data.get('Line No.', item_journal_line.line_no),
                    'item_no': data.get('Item No', item_journal_line.item_no),
                    'posting_date': data.get('Posting Date', item_journal_line.posting_date),
                    'entry_type': data.get('Entry Type', item_journal_line.entry_type),
                    'document_no': data.get('Document No', item_journal_line.document_no),
                    'description': data.get('Description', item_journal_line.description),
                    'location_code': data.get('Location Code', item_journal_line.location_code),
                    'quantity': data.get('Quantity', item_journal_line.quantity),
                    'journal_batch_name': data.get('Journal Batch Name', item_journal_line.journal_batch_name),
                    'qty_calculated': data.get('Qty. (Calculated)', item_journal_line.qty_calculated),
                    'qty_phys_inventory': data.get('Qty. (Phys. Inventory)', item_journal_line.qty_phys_inventory),
                    'phys_inventory': data.get('Phys. Inventory', item_journal_line.phys_inventory),
                    'external_document_no': data.get('External Document No.', item_journal_line.external_document_no),
                    'variant_code': data.get('Variant Code', item_journal_line.variant_code),
                    'qty_per_unit_measure': data.get('Qty. per Unit of Measure', item_journal_line.qty_per_unit_measure),
                    'unit_of_measure_code': data.get('Unit of Measure Code', item_journal_line.unit_of_measure_code),
                    'quantity_base': data.get('Quantity (Base)', item_journal_line.quantity_base)
                })
                return {
                    'message': 'Item Journal Line updated successfully',
                    'response': 200
                }
            else:
                return {
                    'message': 'Item Journal Line not found',
                    'response': 404
                }
        except Exception as e:
            _logger.error("Error updating Item Journal Line: %s", e)
            return {
                'error': str(e),
                'response': 500
            }

    @http.route('/api/tms_item_journal_line/<int:id>', auth='public', methods=['DELETE'], csrf=False, type='json')
    def delete_item_journal_line(self, id, **kw):
        try:
            item_journal_line = request.env['tms.item.journal.line'].sudo().browse(id)
            if item_journal_line.exists():
                item_journal_line.unlink()
                return {
                    'message': 'Item Journal Line deleted successfully',
                    'response': 200
                }
            else:
                return {
                    'message': 'Item Journal Line not found',
                    'response': 404
                }
        except Exception as e:
            _logger.error("Error deleting Item Journal Line: %s", e)
            return {
                'error': str(e),
                'response': 500
            }
