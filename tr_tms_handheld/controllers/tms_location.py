from odoo import http
from odoo.http import request
import logging
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
class TmsLocation(http.Controller):
    @validate_token
    @http.route('/api/tms_location', auth='none', methods=['POST'], csrf=False, type='json')
    def create_location(self, **kw):
        """
        Create new Item or update an existing one
        """
        data = request.jsonrequest

        # Extracting data from the request
        code = data.get('Code')
        name = data.get('Name')
        priority = data.get('Priority')

        tms_location = request.env['tms.locations'].sudo()
        existing_location = tms_location.search([('code', '=', code)])

        try:
            if existing_location:
                existing_location.write({
                    'code': code,
                    'name': name,
                    'priority': priority,
                })
                return {
                    'message': 'Location updated successfully',
                    'response': 200,
                    'Id': existing_location.id
                }
            else:
                tms_location.create({
                    'code': code,
                    'name': name,
                    'priority': priority,
                })
                return {
                    'message': 'Location created successfully',
                    'response': 200,
                }
        except Exception as e:
            _logger.error("Error creating/updating Location: %s", e)
            return {
                'error': str(e),
                'response': 500
            }
