from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class TmsUnitOfMeasures(http.Controller):
    @http.route('/api/tms_uom', auth='none', methods=['POST'], csrf=False, type='json')
    def create_uom(self, **kw):
        """
        Create a new Unit of Measure
        """
        data = request.jsonrequest
        code = data.get('Code')
        description = data.get('Description')

        tms_uom = request.env['tms.unit.of.measures'].sudo()

        if tms_uom.search([('code', '=', code)]):
            uom = tms_uom.search([('code', '=', code)])
            uom.write({
                'code': code,
                'description': description
            })
            return {
                'message': 'Unit of Measure updated successfully',
                'response': 200
            }

        try:
            tms_uom.create({
                'code': code,
                'description': description,
                'code': code
            })
            return {
                'message': 'Unit of Measure created successfully',
                'response': 200
            }
        except Exception as e:
            _logger.error("Error creating Unit of Measure: %s", e)
            return {
                'error': str(e),
                'response': 500
            }
