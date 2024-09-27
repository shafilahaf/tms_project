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

class TmsUnitOfMeasures(http.Controller):
    @validate_token
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
