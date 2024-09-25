from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class TmsItem(http.Controller):
    @http.route('/api/tms_item', auth='none', methods=['POST'], csrf=False, type='json')
    def create_item(self, **kw):
        """
        Create new Item or update an existing one
        """
        data = request.jsonrequest

        # Extracting data from the request
        no = data.get('No.')
        description = data.get('Description')
        search_description = data.get('Search_Description')
        description_2 = data.get('Description_2')
        base_unit_of_measure_id = data.get('Base_Unit_of_Measure')
        inventory_posting_group = data.get('Inventory_Posting_Group')
        vendor_no = data.get('Vendor_No.')
        vendor_item_no = data.get('Vendor_Item_No.')
        manufacturer_code = data.get('Manufacturer_Code')
        item_category_code = data.get('Item_Category_Code')
        product_group_code = data.get('Product_Group_Code')
        item_tracking_code = data.get('Item_Tracking_Code')
        division_code = data.get('Division Code')
        barcode = data.get('Barcode')

        # Extracting tracking flags
        tracking_flags = {
            'man_expir_date_entry_reqd': data.get('Man. Expir. Date Entry Reqd.'),
            'strict_expiration_posting': data.get('Strict Expiration Posting'),
            'sn_specific_tracking': data.get('SN Specific Tracking'),
            'sn_purchase_inbound_tracking': data.get('SN Purchase Inbound Tracking'),
            'sn_purchase_outbound_tracking': data.get('SN Purchase Outbound Tracking'),
            'sn_sales_inbound_tracking': data.get('SN Sales Inbound Tracking'),
            'sn_sales_outbound_tracking': data.get('SN Sales Outbound Tracking'),
            'sn_pos_adjmt_inb_tracking': data.get('SN Pos. Adjmt. Inb. Tracking'),
            'sn_pos_adjmt_outb_tracking': data.get('SN Pos. Adjmt. Outb. Tracking'),
            'sn_neg_adjmt_inb_tracking': data.get('SN Neg. Adjmt. Inb. Tracking'),
            'sn_neg_adjmt_outb_tracking': data.get('SN Neg. Adjmt. Outb. Tracking'),
            'sn_transfer_tracking': data.get('SN Transfer Tracking'),
            'lot_specific_tracking': data.get('Lot Specific Tracking'),
            'lot_purchase_inbound_tracking': data.get('Lot Purchase Inbound Tracking'),
            'lot_purchase_outbound_tracking': data.get('Lot Purchase Outbound Tracking'),
            'lot_sales_inbound_tracking': data.get('Lot Sales Inbound Tracking'),
            'lot_sales_outbound_tracking': data.get('Lot Sales Outbound Tracking'),
            'lot_pos_adjmt_inb_tracking': data.get('Lot Pos. Adjmt. Inb. Tracking'),
            'lot_pos_adjmt_outb_tracking': data.get('Lot Pos. Adjmt. Outb. Tracking'),
            'lot_neg_adjmt_inb_tracking': data.get('Lot Neg. Adjmt. Inb. Tracking'),
            'lot_neg_adjmt_outb_tracking': data.get('Lot Neg. Adjmt. Outb. Tracking'),
            'lot_transfer_tracking': data.get('Lot Transfer Tracking'),
        }

        # Validate required fields
        if not no or not description:
            return {
                'error': 'Code and Description are required',
                'response': 400
            }

        tms_item = request.env['tms.item'].sudo()
        existing_item = tms_item.search([('no', '=', no)])

        try:
            if not item_tracking_code:
                tracking_flags = {key: False for key in tracking_flags}
            else:
                tracking_flags = {key: False if value == "false" else True for key, value in tracking_flags.items()}

            if existing_item:
                existing_item.write({
                    'no': no,
                    'description': description,
                    'search_description': search_description,
                    'description_2': description_2,
                    'base_unit_of_measure_id': base_unit_of_measure_id,
                    'inventory_posting_group': inventory_posting_group,
                    'vendor_no': vendor_no,
                    'vendor_item_no': vendor_item_no,
                    'manufacturer_code': manufacturer_code,
                    'item_category_code': item_category_code,
                    'product_group_code': product_group_code,
                    'item_tracking_code': item_tracking_code,
                    'division_code': division_code,
                    'barcode': barcode,
                    **tracking_flags
                })
                return {
                    'message': 'Item updated successfully',
                    'response': 200
                }
            else:
                tms_item.create({
                    'no': no,
                    'description': description,
                    'search_description': search_description,
                    'description_2': description_2,
                    'base_unit_of_measure_id': base_unit_of_measure_id,
                    'inventory_posting_group': inventory_posting_group,
                    'vendor_no': vendor_no,
                    'vendor_item_no': vendor_item_no,
                    'manufacturer_code': manufacturer_code,
                    'item_category_code': item_category_code,
                    'product_group_code': product_group_code,
                    'item_tracking_code': item_tracking_code,
                    'division_code': division_code,
                    'barcode': barcode,
                    **tracking_flags
                })
                return {
                    'message': 'Item created successfully',
                    'response': 200
                }
        except Exception as e:
            _logger.error("Error creating/updating Item: %s", e)
            return {
                'error': str(e),
                'response': 500
            }
