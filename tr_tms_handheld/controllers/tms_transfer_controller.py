from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class TmsTransferHeader(http.Controller):

    @http.route('/api/tms_transfer_header', auth='public', methods=['POST'], csrf=False, type='json')
    def create_transfer(self, **kw):
        try:
            data = request.jsonrequest
            no = data.get('No')
            transfer_from_code = data.get('Transfer-from Code')
            transfer_from_name = data.get('Transfer-from Name')
            transfer_from_name_2 = data.get('Transfer-from Name 2')
            transfer_from_address = data.get('Transfer-from Address')
            transfer_from_address_2 = data.get('Transfer-from Address 2')
            transfer_from_post_code = data.get('Transfer-from Post Code')
            transfer_from_city = data.get('Transfer-from City')
            transfer_from_county = data.get('Transfer-from County')
            transfer_from_country_region_code = data.get('Trsf.-from Country/Region Code')
            transfer_to_code = data.get('Transfer-to Code')
            transfer_to_name = data.get('Transfer-to Name')
            transfer_to_name_2 = data.get('Transfer-to Name 2')
            transfer_to_address = data.get('Transfer-to Address')
            transfer_to_address_2 = data.get('Transfer-to Address 2')
            transfer_to_post_code = data.get('Transfer-to Post Code')
            transfer_to_city = data.get('Transfer-to City')
            transfer_to_county = data.get('Transfer-to County')
            transfer_to_country_region_code = data.get('Trsf.-to Country/Region Code')
            posting_date = data.get('Posting Date')
            shipment_date = data.get('Shipment Date')
            receipt_date = data.get('Receipt Date')
            status = data.get('Status')
            comment = data.get('Comment')
            in_transit_code = data.get('In-Transit Code')
            external_document_no = data.get('External Document No.')
            completely_shipped = data.get('Completely Shipped')
            completely_received = data.get('Completely Received')
            assigned_user_id = data.get('Assigned User ID')
            keterangan = data.get('Keterangan')
            supplier_no_packing_list = data.get('Supplier & No Packing List')
            customer_no = data.get('Customer No.')
            salesperson_code = data.get('Salesperson Code')
            location_sales_type = data.get('Location Sales Type')
            shipment_no_series = data.get('Shipment No Series')
            store_to = data.get('Store-to')
            transfer_type = data.get('Transfer Type')

            # Check if the transfer order already exists
            tms_transfer = request.env['tms.transfer.header'].sudo()
            transfer_order = tms_transfer.search([('no', '=', no)])

            if transfer_order:
                # Update existing transfer order
                transfer_order.write({
                    'transfer_from_code': transfer_from_code,
                    'transfer_from_name': transfer_from_name,
                    'transfer_from_name_2': transfer_from_name_2,
                    'transfer_from_address': transfer_from_address,
                    'transfer_from_address_2': transfer_from_address_2,
                    'transfer_from_post_code': transfer_from_post_code,
                    'transfer_from_city': transfer_from_city,
                    'transfer_from_county': transfer_from_county,
                    'transfer_from_country_region_code': transfer_from_country_region_code,
                    'transfer_to_code': transfer_to_code,
                    'transfer_to_name': transfer_to_name,
                    'transfer_to_name_2': transfer_to_name_2,
                    'transfer_to_address': transfer_to_address,
                    'transfer_to_address_2': transfer_to_address_2,
                    'transfer_to_post_code': transfer_to_post_code,
                    'transfer_to_city': transfer_to_city,
                    'transfer_to_county': transfer_to_county,
                    'transfer_to_country_region_code': transfer_to_country_region_code,
                    'posting_date': posting_date,
                    'shipment_date': shipment_date,
                    'receipt_date': receipt_date,
                    'status': status,
                    'comment': comment,
                    'in_transit_code': in_transit_code,
                    'external_document_no': external_document_no,
                    'completely_shipped': completely_shipped,
                    'completely_received': completely_received,
                    'assigned_user_id': assigned_user_id,
                    'keterangan': keterangan,
                    'supplier_no_packing_list': supplier_no_packing_list,
                    'customer_no': customer_no,
                    'salesperson_code': salesperson_code,
                    'location_sales_type': location_sales_type,
                    'shipment_no_series': shipment_no_series,
                    'store_to': store_to,
                    'transfer_type': transfer_type
                })
            else:
                # Create new transfer order
                transfer_order = tms_transfer.create({
                    'no': no,
                    'transfer_from_code': transfer_from_code,
                    'transfer_from_name': transfer_from_name,
                    'transfer_from_name_2': transfer_from_name_2,
                    'transfer_from_address': transfer_from_address,
                    'transfer_from_address_2': transfer_from_address_2,
                    'transfer_from_post_code': transfer_from_post_code,
                    'transfer_from_city': transfer_from_city,
                    'transfer_from_county': transfer_from_county,
                    'transfer_from_country_region_code': transfer_from_country_region_code,
                    'transfer_to_code': transfer_to_code,
                    'transfer_to_name': transfer_to_name,
                    'transfer_to_name_2': transfer_to_name_2,
                    'transfer_to_address': transfer_to_address,
                    'transfer_to_address_2': transfer_to_address_2,
                    'transfer_to_post_code': transfer_to_post_code,
                    'transfer_to_city': transfer_to_city,
                    'transfer_to_county': transfer_to_county,
                    'transfer_to_country_region_code': transfer_to_country_region_code,
                    'posting_date': posting_date,
                    'shipment_date': shipment_date,
                    'receipt_date': receipt_date,
                    'status': status,
                    'comment': comment,
                    'in_transit_code': in_transit_code,
                    'external_document_no': external_document_no,
                    'completely_shipped': completely_shipped,
                    'completely_received': completely_received,
                    'assigned_user_id': assigned_user_id,
                    'keterangan': keterangan,
                    'supplier_no_packing_list': supplier_no_packing_list,
                    'customer_no': customer_no,
                    'salesperson_code': salesperson_code,
                    'location_sales_type': location_sales_type,
                    'shipment_no_series': shipment_no_series,
                    'store_to': store_to,
                    'transfer_type': transfer_type
                })

            return {
                'message': 'Transfer Order created/updated successfully',
                'response': 200
            }
        except Exception as e:
            _logger.error("Error creating Transfer Order: %s", e)
            return {
                'error': str(e),
                'response': 500
            }

class TmsTransferLine(http.Controller):

    @http.route('/api/tms_transfer_line', auth='public', methods=['POST'], csrf=False, type='json')
    def create_transfer_line(self, **kw):
        try:
            data = request.jsonrequest
            header_id = data.get('header_id')
            transfer_lines = data.get('Transfer_Lines', [])

            if not header_id:
                return {
                    'error': 'Transfer Order ID is required',
                    'response': 400
                }

            transfer_order = request.env['tms.transfer.header'].sudo().browse(header_id)

            if not transfer_order:
                return {
                    'error': 'Transfer Order not found',
                    'response': 404
                }

            # Create or update transfer lines
            for line_data in transfer_lines:
                line_values = {
                    'header_id': transfer_order.id,
                    'document_no': transfer_order.no,
                    'line_no': line_data.get('Line No.'),
                    'item_no': line_data.get('Item No.'),
                    'quantity': line_data.get('Quantity'),
                    'uom': line_data.get('Unit of Measure'),
                    'qty_to_ship': line_data.get('Qty. to Ship'),
                    'qty_to_receive': line_data.get('Qty. to Receive'),
                    'qty_shipped': line_data.get('Quantity Shipped'),
                    'qty_received': line_data.get('Quantity Received'),
                    'status': line_data.get('Status'),
                    'description': line_data.get('Description'),
                    'quantity_base': line_data.get('Quantity (Base)'),
                    'outstanding_qty_base': line_data.get('Outstanding Qty. (Base)'),
                    'qty_to_ship_base': line_data.get('Qty. to Ship (Base)'),
                    'qty_shipped_base': line_data.get('Qty. Shipped (Base)'),
                    'qty_to_receive_base': line_data.get('Qty. to Receive (Base)'),
                    'qty_received_base': line_data.get('Qty. Received (Base)'),
                    'qty_per_uom': line_data.get('Qty. per Unit of Measure'),
                    'uom_code': line_data.get('Unit of Measure Code'),
                    'outstanding_quantity': line_data.get('Outstanding Quantity'),
                    'variant_code': line_data.get('Variant Code'),
                    'description_2': line_data.get('Description 2'),
                    'in_transit_code': line_data.get('In-Transit Code'),
                    'qty_in_transit': line_data.get('Qty. in Transit'),
                    'qty_in_transit_base': line_data.get('Qty. in Transit (Base)'),
                    'transfer_from_code': line_data.get('Transfer-from Code'),
                    'transfer_to_code': line_data.get('Transfer-to Code'),
                    'shipment_date': line_data.get('Shipment Date'),
                    'derived_from_line_no': line_data.get('Derived From Line No.'),
                    'keterangan_dus': line_data.get('Keterangan Dus'),
                }

                transfer_line = request.env['tms.transfer.line'].sudo().search([
                    ('header_id', '=', transfer_order.id),
                    ('line_no', '=', line_values['line_no'])
                ])

                if transfer_line:
                    transfer_line.write(line_values)
                else:
                    request.env['tms.transfer.line'].sudo().create(line_values)

            return {
                'message': 'Transfer Lines created/updated successfully',
                'response': 200
            }
        except Exception as e:
            _logger.error("Error creating Transfer Lines: %s", e)
            return {
                'error': str(e),
                'response': 500
            }