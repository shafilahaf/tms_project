from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class TMSReservationEntryController(http.Controller):
    @http.route('/api/tms_reservation_entry', auth='public', methods=['POST'], csrf=False, type='json')
    def create_reservation_entry(self, **kw):
        try:
            data = request.jsonrequest
            # Extract fields from the request
            entry_no = data.get('Entry No')
            item_no = data.get('Item No')
            location_code = data.get('Location Code')
            quantity_base = data.get('Quantity Base')
            reservation_status = data.get('Reservation Status')
            source_type = data.get('Source Type')
            source_subtype = data.get('Source Subtype')
            source_id = data.get('Source Id')
            source_batch_name = data.get('Source Batch Name')
            source_ref_no = data.get('Source Ref. No.')
            positive = data.get('Positive')
            quantity = data.get('Quantity')
            expiration_date = data.get('Expiration Date')
            qty_to_handle_base = data.get('Qty To Handle Base')
            lot_no = data.get('Lot No.')
            item_tracking = data.get('Item Tracking')

            # Create a new reservation entry
            reservation_entry = request.env['tms.reservation.entry'].create({
                'entry_no': entry_no,
                'item_no': item_no,
                'location_code': location_code,
                'quantity_base': quantity_base,
                'reservation_status': reservation_status,
                'source_type': source_type,
                'source_subtype': source_subtype,
                'source_id': source_id,
                'source_batch_name': source_batch_name,
                'source_ref_no': source_ref_no,
                'positive': positive,
                'quantity': quantity,
                'expiration_date': expiration_date,
                'qty_to_handle_base': qty_to_handle_base,
                'lot_no': lot_no,
                'item_tracking': item_tracking
            })

            return {
                'message': 'Reservation Entry created successfully',
                'response': 200,
                'id': reservation_entry.id
            }
        except Exception as e:
            _logger.error("Error creating Reservation Entry: %s", e)
            return {
                'error': str(e),
                'response': 500
            }

    @http.route('/api/tms_reservation_entry/<int:id>', auth='public', methods=['GET'], csrf=False, type='json')
    def get_reservation_entry(self, id, **kw):
        try:
            reservation_entry = request.env['tms.reservation.entry'].browse(id)
            if not reservation_entry.exists():
                return {
                    'error': 'Reservation Entry not found',
                    'response': 404
                }
            return reservation_entry.read()[0]
        except Exception as e:
            _logger.error("Error retrieving Reservation Entry: %s", e)
            return {
                'error': str(e),
                'response': 500
            }

    @http.route('/api/tms_reservation_entry/<int:id>', auth='public', methods=['PUT'], csrf=False, type='json')
    def update_reservation_entry(self, id, **kw):
        try:
            data = request.jsonrequest
            reservation_entry = request.env['tms.reservation.entry'].browse(id)
            if not reservation_entry.exists():
                return {
                    'error': 'Reservation Entry not found',
                    'response': 404
                }
            reservation_entry.write(data)
            return {
                'message': 'Reservation Entry updated successfully',
                'response': 200
            }
        except Exception as e:
            _logger.error("Error updating Reservation Entry: %s", e)
            return {
                'error': str(e),
                'response': 500
            }

    @http.route('/api/tms_reservation_entry/<int:id>', auth='public', methods=['DELETE'], csrf=False, type='json')
    def delete_reservation_entry(self, id, **kw):
        try:
            reservation_entry = request.env['tms.reservation.entry'].browse(id)
            if not reservation_entry.exists():
                return {
                    'error': 'Reservation Entry not found',
                    'response': 404
                }
            reservation_entry.unlink()
            return {
                'message': 'Reservation Entry deleted successfully',
                'response': 200
            }
        except Exception as e:
            _logger.error("Error deleting Reservation Entry: %s", e)
            return {
                'error': str(e),
                'response': 500
            }
