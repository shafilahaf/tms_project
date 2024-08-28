from odoo import http
import json
class OdooAPIController(http.Controller):
    @http.route('/api/endpoint', type='json')
    def api_endpoint(self, **kw):
        # Access the request parameters
        parameters = json.loads(http.request.httprequest.data)
        # Process the API request and return the response
        response = {
            'status': 'success',
            'message': 'API request received without authentication TR2',
            'data': {
                'parameters': parameters
            }
        }
        return response
