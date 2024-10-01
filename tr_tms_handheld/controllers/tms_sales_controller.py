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

class TmssalesHeader(http.Controller):
    @validate_token
    @http.route('/api/tms_sales_order', auth='public', methods=['POST'], csrf=False, type='json')
    def create_sales_order(self, **kw):
        try:
            data = request.jsonrequest
            document_type = data.get('Document Type')
            sell_to_customer_no = data.get('Sell-to Customer No.')
            no = data.get('No.')
            order_date = data.get('Order Date')
            posting_date = data.get('Posting Date')
            shipment_date = data.get('Shipment Date')
            location_code = data.get('Location Code')
            sell_to_customer_name = data.get('Sell-to Customer Name')
            sell_to_customer_name_2 = data.get('Sell-to Customer Name 2')
            sell_to_address = data.get('Sell-to Address')
            sell_to_address_2 = data.get('Sell-to Address 2')
            sell_to_city = data.get('Sell-to City')
            sell_to_contact = data.get('Sell-to Contact')
            sell_to_post_code = data.get('Sell-to Post Code')
            sell_to_county = data.get('Sell-to County')
            sell_to_country_region_code = data.get('Sell-to Country/Region Code')
            ship_to_post_code = data.get('Ship-to Post Code')
            ship_to_county = data.get('Ship-to County')
            ship_to_country_region_code = data.get('Ship-to Country/Region Code')
            shipping_agent_code = data.get('Shipping Agent Code')
            package_tracking_no = data.get('Package Tracking No.')
            posting_no_series = data.get('Posting No. Series')
            shipping_no_series = data.get('Shipping No. Series')
            status = data.get('Status')
            return_receipt_no_series = data.get('Return Receipt No. Series')
            store_no = data.get('Store No.')
            complete_shipment = data.get('Complete Shipment')

            tms_sales = request.env['tms.sales.order.header'].sudo()
            tms_sales_line = request.env['tms.sales.order.line'].sudo()
            sales_order = tms_sales.search([('document_type', '=', document_type), ('no', '=', no)])

            if sales_order:

                tms_sales_line.search([('header_id', '=', sales_order.id)]).unlink()

                sales_order.write({
                    'document_type': document_type,
                    'sell_to_customer_no': sell_to_customer_no,
                    'no': no,
                    'order_date': order_date,
                    'posting_date': posting_date,
                    'shipment_date': shipment_date,
                    'location_code': location_code,
                    'sell_to_customer_name': sell_to_customer_name,
                    'sell_to_customer_name_2': sell_to_customer_name_2,
                    'sell_to_address': sell_to_address,
                    'sell_to_address_2': sell_to_address_2,
                    'sell_to_city': sell_to_city,
                    'sell_to_contact': sell_to_contact,
                    'sell_to_post_code': sell_to_post_code,
                    'sell_to_county': sell_to_county,
                    'sell_to_country_region_code': sell_to_country_region_code,
                    'ship_to_post_code': ship_to_post_code,
                    'ship_to_county': ship_to_county,
                    'ship_to_country_region_code': ship_to_country_region_code,
                    'shipping_agent_code': shipping_agent_code,
                    'package_tracking_no': package_tracking_no,
                    'posting_no_series': posting_no_series,
                    'shipping_no_series': shipping_no_series,
                    'status': status,
                    'return_receipt_no_series': return_receipt_no_series,
                    'store_no': store_no,
                    'complete_shipment': False if complete_shipment == "false" else True,
                })
            else:
                sales_order = tms_sales.create({
                    'document_type': document_type,
                    'sell_to_customer_no': sell_to_customer_no,
                    'no': no,
                    'order_date': order_date,
                    'posting_date': posting_date,
                    'shipment_date': shipment_date,
                    'location_code': location_code,
                    'sell_to_customer_name': sell_to_customer_name,
                    'sell_to_customer_name_2': sell_to_customer_name_2,
                    'sell_to_address': sell_to_address,
                    'sell_to_address_2': sell_to_address_2,
                    'sell_to_city': sell_to_city,
                    'sell_to_contact': sell_to_contact,
                    'sell_to_post_code': sell_to_post_code,
                    'sell_to_county': sell_to_county,
                    'sell_to_country_region_code': sell_to_country_region_code,
                    'ship_to_post_code': ship_to_post_code,
                    'ship_to_county': ship_to_county,
                    'ship_to_country_region_code': ship_to_country_region_code,
                    'shipping_agent_code': shipping_agent_code,
                    'package_tracking_no': package_tracking_no,
                    'posting_no_series': posting_no_series,
                    'shipping_no_series': shipping_no_series,
                    'status': status,
                    'return_receipt_no_series': return_receipt_no_series,
                    'store_no': store_no,
                    'complete_shipment': False if complete_shipment == "false" else True,
                })

            return {
                'message': 'sales Order created/updated successfully',
                'response': 200,
                'header_id': sales_order.id
            }
        except Exception as e:
            _logger.error("Error creating/updating sales Order Header: %s", e)
            return {
                'error': str(e),
                'response': 500
            }

class TmsSalesLine(http.Controller):
    @validate_token
    @http.route('/api/tms_sales_order_line', auth='public', methods=['POST'], csrf=False, type='json')
    def create_sales_order_line(self, **kw):
        try:
            data = request.jsonrequest
            header_id = data.get('header_id')
            sales_order_lines = data.get('Sales_Order_Lines', [])
            
            if not header_id:
                return {
                    'error': 'Sales Order ID is required',
                    'response': 400
                }

            sales_order = request.env['tms.sales.order.header'].sudo().browse(header_id)

            if not sales_order:
                return {
                    'error': 'Sales Order not found',
                    'response': 404
                }

            tms_sales_line = request.env['tms.sales.order.line'].sudo()
            tms_item_model = request.env['tms.item'].sudo()

            # Create or update sales order lines
            for line_data in sales_order_lines:
                item_no = line_data.get('No.')
                item_record = tms_item_model.search([('no', '=', item_no)], limit=1)
            
                line_values = {
                    'header_id': header_id,
                    'line_no': line_data.get('Line No.'),
                    'document_type': line_data.get('Document Type'),
                    'sell_to_customer_no': line_data.get('Sell-to Customer No.'),
                    'document_no': line_data.get('Document No.'),
                    'type': line_data.get('Type'),
                    'no': str(item_record.id) if item_record else False,
                    'location_code': line_data.get('Location Code'),
                    'description': line_data.get('Description'),
                    'description_2': line_data.get('Description 2'),
                    'unit_of_measure': line_data.get('Unit Of Measure'),
                    'quantity': line_data.get('Quantity'),
                    'outstanding_quantity': line_data.get('Outstanding Quantity'),
                    'qty_to_ship': line_data.get('Qty To Ship'),
                    'quantity_shipped': line_data.get('Quantity Shipped'),
                    'variant_code': line_data.get('Variant Code'),
                    'qty_per_unit_of_measure': line_data.get('Qty. per Unit of Measure'),
                    'unit_of_measure_code': line_data.get('Unit of Measure Code'),
                    'quantity_base': line_data.get('Quantity (Base)'),
                    'outstanding_qty_base': line_data.get('Outstanding Qty. (Base)'),
                    'qty_to_invoice_base': line_data.get('Qty. to Invoice (Base)'),
                    'qty_to_ship_base': line_data.get('Qty. to Ship (Base)'),
                    'qty_shipped_not_invd_base': line_data.get('Qty. Shipped Not Invd. (Base)'),
                    'qty_shipped_base': line_data.get('Qty. Shipped (Base)'),
                    'qty_invoiced_base': line_data.get('Qty. Invoiced (Base)'),
                    'return_qty_to_receive': line_data.get('Return Qty. to Receive'),
                    'return_qty_to_receive_base': line_data.get('Return Qty. to Receive (Base)'),
                    'return_qty_rcd_not_invd': line_data.get('Return Qty. Rcd. Not Invd.'),
                    'return_qty_rcd_not_invd_base': line_data.get('Return Qty. Rcd. Not Invd.(Base)'),
                    'return_qty_received': line_data.get('Return Qty. Received'),
                    'return_qty_received_base': line_data.get('Return Qty. Received (Base)'),
                    'return_reason_code': line_data.get('Return Reason Code'),
                    'item_no_no': item_no,
                }

              
                tms_sales_line.create(line_values)

            return {
                'message': 'Sales Order Lines created/updated successfully',
                'response': 200
            }
        except Exception as e:
            _logger.error("Error creating Sales Order Lines: %s", e)
            return {
                'error': str(e),
                'response': 500
            }