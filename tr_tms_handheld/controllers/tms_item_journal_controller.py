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

class TmsItemJournal(http.Controller):
    @validate_token
    @http.route('/api/tms_item_journal', auth='public', methods=['POST'], csrf=False, type='json')
    def create_item_journal(self, **kw):
        try:
            data = request.jsonrequest
            no = data.get('No')
            document_type = data.get('Document_Type')
            posting_date = data.get('Posting_Date')
            location_code = data.get('Location_Code')
            journal_template_name = data.get('Journal_Template_Name')
            journal_batch_name = data.get('Journal_Batch_Name')
            status = data.get('Status')

            tms_item_journal = request.env['tms.item.journal'].sudo()
            journal = tms_item_journal.search([('no', '=', no)])
            tms_item_journal_line = request.env['tms.item.journal.line'].sudo()

            tms_location = request.env['tms.locations'].sudo()
            rec_loc = tms_location.search([
                ('code','=',location_code)
            ])

            if journal:
                
                tms_item_journal_line.search([('header_id', '=', journal.id)]).unlink()

                journal.write({
                    'no': no,
                    'document_type': document_type,
                    'posting_date': posting_date,
                    'location_code': rec_loc.id,
                    'journal_template_name': journal_template_name,
                    'journal_batch_name': journal_batch_name,
                    'status': status,
                })
            else:
                journal = tms_item_journal.create({
                    'no': no,
                    'document_type': document_type,
                    'posting_date': posting_date,
                    'location_code': rec_loc.id,
                    'journal_template_name': journal_template_name,
                    'journal_batch_name': journal_batch_name,
                    'status': status,
                })

            return {
                'message': 'Item Journal created/updated successfully',
                'response': 200,
                'item_journal_id': journal.id
            }
        except Exception as e:
            _logger.error("Error creating/updating Item Journal Header: %s", e)
            return {
                'error': str(e),
                'response': 500
            }

class TmsItemJournalLine(http.Controller):
    @validate_token
    @http.route('/api/tms_item_journal_line', auth='public', methods=['POST'], csrf=False, type='json')
    def create_item_journal_line(self, **kw):
        try:
            data = request.jsonrequest
            header_id = data.get('header_id')
            item_journal_lines = data.get('Item_Journal_Lines', [])

            if not header_id:
                return {
                    'error': 'Item Journal ID is required',
                    'response': 400
                }

            item_journal = request.env['tms.item.journal'].sudo().browse(header_id)

            if not item_journal:
                return {
                    'error': 'Item Journal not found',
                    'response': 404
                }

            item_journal_line = request.env['tms.item.journal.line'].sudo()
            tms_item_model = request.env['tms.item'].sudo()
            tms_uom_model = request.env['tms.unit.of.measures'].sudo()

            for line_data in item_journal_lines:
                item_no = line_data.get('Item No. Code')
                item_record = tms_item_model.search([('no', '=', item_no)], limit=1)
                
                uom_code = line_data.get('Unit of Measure Code')
                uom_record_code = tms_uom_model.search([('code', '=', uom_code)], limit=1)
                
                line_values = {
                    'header_id': header_id,
                    'document_no': line_data.get('Document No.'),
                    'line_no': line_data.get('Line No.'),
                    'posting_date':  line_data.get('Posting Date'),
                    'entry_type': line_data.get('Entry Type'),
                    'item_no_code': str(item_record.id) if item_record else False,
                    'description' : line_data.get('Description'),
                    'unit_of_measure_code': str(uom_record_code.id) if uom_record_code else False,
                    'quantity': line_data.get('Quantity'),
                }

                item_journal_line.create(line_values)

            return {
                'message': 'Item Journal Lines created/updated successfully',
                'response': 200
             }
        except Exception as e:
            _logger.error("Error creating/updating Item Journal Lines: %s", e)
            return {
                'error': str(e),
                'response': 500
            }
