from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class TmsItemUoM(http.Controller):
    @http.route('/api/tms_item_uom', auth='none', methods=['POST'], csrf=False, type='json')
    def create_item_uom(self, **kw):
        """
        Create a new Item Unit of Measure
        """
        data = request.jsonrequest
        code = data.get('Code')
        item_no = data.get('Item_No.')
        qty_per_unit_of_measure = data.get('Qty_per_Unit_of_Measure')
        
        if not code or not item_no:
            return {
                'error': 'Code and Item No. are required',
                'response': 400
            }

        tms_item_uom = request.env['tms.item.uom'].sudo()

        if tms_item_uom.search([('code', '=', code)]):
            uom = tms_item_uom.search([('code', '=', code)])
            uom.write({
                'code': code,
                'item_no': item_no,
                'qty_per_unit_of_measure': qty_per_unit_of_measure
            })
            return {
                'message': 'Item UoM updated successfully',
                'response': 200
            }

        try:
            tms_item_uom.create({
                'code': code,
                'item_no': item_no,
                'qty_per_unit_of_measure': qty_per_unit_of_measure
            })
            return {
                'message': 'Item UoM created successfully',
                'response': 200
            }
        except Exception as e:
            _logger.error("Error creating Item UoM: %s", e)
            return {
                'error': str(e),
                'response': 500
            }
