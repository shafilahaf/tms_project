from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class TmsPurchaseHeader(http.Controller):
    @http.route('/api/tms_purchase_order', auth='public', methods=['POST'], csrf=False, type='json')
    def create_purchase_order(self, **kw):
        try:
            data = request.jsonrequest
            document_type = data.get('Document Type')
            buy_from_vendor_no = data.get('Buy-from Vendor No.')
            no = data.get('No.')
            order_date = data.get('Order Date')
            posting_date = data.get('Posting Date')
            location_code = data.get('Location Code')
            vendor_shipment_no = data.get('Vendor Shipment No.')
            buy_from_vendor_name = data.get('Buy-from Vendor Name')
            buy_from_vendor_name_2 = data.get('Buy-from Vendor Name 2')
            buy_from_address = data.get('Buy-from Address')
            buy_from_address_2 = data.get('Buy-from Address 2')
            buy_from_city = data.get('Buy-from City')
            buy_from_contact = data.get('Buy-from Contact')
            buy_from_post_code = data.get('Buy-from Post Code')
            buy_from_country = data.get('Buy-from Country')
            buy_from_country_region_code = data.get('Buy-from Country/Region Code')
            no_series = data.get('No. Series')
            posting_no_series = data.get('Posting No. Series')
            receiving_no_series = data.get('Receiving No. Series')
            status = data.get('Status')
            return_shipment_no = data.get('Return Shipment No.')
            return_shipment_no_series = data.get('Return Shipment No. Series')
            store_no = data.get('Store No.')
            complete_received = data.get('Complete Received')
            # po_reopen = data.get('ReOpen')

            tms_purchase = request.env['tms.purchase.order.header'].sudo()
            purchase_order = tms_purchase.search([('document_type', '=', document_type), ('no', '=', no)])
            tms_purchase_line = request.env['tms.purchase.order.line'].sudo()

            if purchase_order:
                
                tms_purchase_line.search([('header_id', '=', purchase_order.id)]).unlink()
                
                purchase_order.write({
                    'document_type': document_type,
                    'buy_from_vendor_no': buy_from_vendor_no,
                    'no': no,
                    'order_date': order_date,
                    'posting_date': posting_date,
                    'location_code': location_code,
                    'vendor_shipment_no': vendor_shipment_no,
                    'buy_from_vendor_name': buy_from_vendor_name,
                    'buy_from_vendor_name_2': buy_from_vendor_name_2,
                    'buy_from_address': buy_from_address,
                    'buy_from_address_2': buy_from_address_2,
                    'buy_from_city': buy_from_city,
                    'buy_from_contact': buy_from_contact,
                    'buy_from_post_code': buy_from_post_code,
                    'buy_from_country': buy_from_country,
                    'buy_from_country_region_code': buy_from_country_region_code,
                    'no_series': no_series,
                    'posting_no_series': posting_no_series,
                    'receiving_no_series': receiving_no_series,
                    'status': status,
                    'return_shipment_no': return_shipment_no,
                    'return_shipment_no_series': return_shipment_no_series,
                    'store_no': store_no,
                    'complete_received': False if complete_received == "false" else True,
                    # 'po_reopen': False if po_reopen == "false" else True
                })
            else:
                purchase_order = tms_purchase.create({
                    'document_type': document_type,
                    'buy_from_vendor_no': buy_from_vendor_no,
                    'no': no,
                    'order_date': order_date,
                    'posting_date': posting_date,
                    'location_code': location_code,
                    'vendor_shipment_no': vendor_shipment_no,
                    'buy_from_vendor_name': buy_from_vendor_name,
                    'buy_from_vendor_name_2': buy_from_vendor_name_2,
                    'buy_from_address': buy_from_address,
                    'buy_from_address_2': buy_from_address_2,
                    'buy_from_city': buy_from_city,
                    'buy_from_contact': buy_from_contact,
                    'buy_from_post_code': buy_from_post_code,
                    'buy_from_country': buy_from_country,
                    'buy_from_country_region_code': buy_from_country_region_code,
                    'no_series': no_series,
                    'posting_no_series': posting_no_series,
                    'receiving_no_series': receiving_no_series,
                    'status': status,
                    'return_shipment_no': return_shipment_no,
                    'return_shipment_no_series': return_shipment_no_series,
                    'store_no': store_no,
                    'complete_received': False if complete_received == "false" else True,
                    # 'po_reopen': False if po_reopen == "false" else True
                })

            return {
                'message': 'Purchase Order created/updated successfully',
                'response': 200,
                'purchase_order_id': purchase_order.id
            }
        except Exception as e:
            _logger.error("Error creating/updating Purchase Order Header: %s", e)
            return {
                'error': str(e),
                'response': 500
            }

class TmsPurchaseLine(http.Controller):
    @http.route('/api/tms_purchase_order_line', auth='public', methods=['POST'], csrf=False, type='json')
    def create_purchase_order_line(self, **kw):
        try:
            data = request.jsonrequest
            header_id = data.get('header_id')
            purchase_order_lines = data.get('Purchase_Order_Lines', [])

            tms_purchase_line = request.env['tms.purchase.order.line'].sudo()
            tms_item_model = request.env['tms.item'].sudo()
            tms_uom_model = request.env['tms.unit.of.measures'].sudo()

            for line_data in purchase_order_lines:
                item_no = line_data.get('No.')
                item_record = tms_item_model.search([('no', '=', item_no)], limit=1)
                
                uom = line_data.get('Unit Of Measure')
                uom_code = line_data.get('Unit of Measure Code')
                uom_record = tms_uom_model.search([('code', '=', uom)], limit=1)
                uom_record_code = tms_uom_model.search([('code', '=', uom_code)], limit=1)
                
                line_values = {
                    'header_id': header_id,
                    'line_no': line_data.get('Line No.'),
                    'document_type': line_data.get('Document Type'),
                    'buy_from_vendor_no': line_data.get('Buy From Vendor No.'),
                    'document_no': line_data.get('Document No.'),
                    'type': line_data.get('Type'),
                    'no': str(item_record.id) if item_record else False,
                    'location_code': line_data.get('Location Code'),
                    'description': line_data.get('Description'),
                    'description_2': line_data.get('Description 2'),
                    'unit_of_measure': str(uom_record.id) if uom_record else False,
                    'quantity': line_data.get('Quantity'),
                    'outstanding_quantity': line_data.get('Outstanding Quantity'),
                    'qty_to_receive': line_data.get('Qty To Receive'),
                    'qty_received': line_data.get('Qty Received'),
                    'variant_code': line_data.get('Variant Code'),
                    'qty_per_unit_of_measure': line_data.get('Qty. per Unit of Measure'),
                    'unit_of_measure_code': str(uom_record_code.id) if uom_record_code else False,
                    'quantity_base': line_data.get('Quantity (Base)'),
                    'outstanding_qty_base': line_data.get('Outstanding Qty. (Base)'),
                    'qty_to_invoice_base': line_data.get('Qty. to Invoice (Base)'),
                    'qty_to_receive_base': line_data.get('Qty. to Receive (Base)'),
                    'qty_rcd_not_invoiced_base': line_data.get('Qty. Rcd. Not Invoiced (Base)'),
                    'qty_received_base': line_data.get('Qty. Received (Base)'),
                    'qty_invoiced_base': line_data.get('Qty. Invoiced (Base)'),
                    'return_qty_to_ship': line_data.get('Return Qty. to Ship'),
                    'return_qty_to_ship_base': line_data.get('Return Qty. to Ship (Base)'),
                    'return_qty_shipped_not_invd': line_data.get('Return Qty. Shipped Not Invd.'),
                    'ret_qty_shpd_not_invd_base': line_data.get('Ret. Qty. Shpd Not Invd.(Base)'),
                    'return_qty_shipped': line_data.get('Return Qty. Shipped'),
                    'return_qty_shipped_base': line_data.get('Return Qty. Shipped (Base)'),
                    'return_reason_code': line_data.get('Return Reason Code'),
                    'notes': line_data.get('Notes'),
                }

                existing_line = tms_purchase_line.search([('header_id', '=', header_id), ('line_no', '=', line_values['line_no'])])
                if existing_line:
                    existing_line.write(line_values)
                else:
                    tms_purchase_line.create(line_values)

            return {
                'message': 'Purchase Order Lines created/updated successfully',
                'response': 200
            }
        except Exception as e:
            _logger.error("Error creating/updating Purchase Order Lines: %s", e)
            return {
                'error': str(e),
                'response': 500
            }
