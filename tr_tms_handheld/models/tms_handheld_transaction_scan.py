from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from requests_ntlm2 import HttpNtlmAuth
import requests
import re
from datetime import datetime


class TMSHandheldTransactionScan(models.Model):
    _name = 'tms.handheld.transaction.scan'
    _description = 'TMS Purchase Scan Item'
    _rec_name = 'handheld_transaction_id'
    
    barcode_code = fields.Char(string="Scan Barcode")
    handheld_transaction_id = fields.Many2one('tms.handheld.transaction', string='Purchase Receipt')
    item_no = fields.Many2one('tms.item', string="Item No.", domain="[('id', 'in', available_item_ids)]")
    item_description = fields.Char('Item Description', readonly=True, store=True)
    quantity =  fields.Float('Quantity')
    reservation_entry_ids = fields.One2many('tms.reservation.entry', 'purchase_scan_id', string='Reservation Entry')
    item_tracking_code = fields.Char(string='Item Tracking Code', related='item_no.item_tracking_code')
    
    available_item_ids = fields.Many2many('tms.item', compute='_compute_available_item_ids', store=False)

    contains_sn = fields.Boolean(compute='_compute_contains_sn', store=True)
    contains_lot = fields.Boolean(compute='_compute_contains_lot', store=True)
    contains_lot_sn = fields.Boolean(compute='_compute_contains_snlot', store=True)

    serial_number = fields.Char('Serial No.')
    exp_date = fields.Date('Exp Date')
    lot_number = fields.Char('Lot No.')

    item_uom = fields.Many2one('tms.item.uom', string="Unit of Measure",domain="[('item_no', '=', item_no_no)]")
    item_no_no = fields.Char(string='Item Number', store=True)
    line_po = fields.Many2one('tms.purchase.order.line',string ='Line No.',domain = "[('document_no', '=', source_doc_no),('item_no_no', '=', item_no_no)]")
    line_so = fields.Many2one('tms.sales.order.line', string="Line No.", domain = "[('document_no', '=', source_doc_no),('item_no_no', '=', item_no_no)]")
    line_to = fields.Many2one('tms.transfer.line', string="Line No.", domain = "[('document_no', '=', source_doc_no),('item_no_no', '=', item_no_no)]")
    source_doc_no = fields.Char('Source Doc. No.', readonly=True)
    handheld_document_type = fields.Selection([('1', 'Purchase Receipt Order'), ('2', 'Purchase Return Shipment'),('3', 'Sales Shipment Order'), ('4', 'Sales Return Receipt'), ('5', 'Transfer Shipment'),('6', 'Transfer Receipt'),('8', 'Item Journal')], string='Document Type')
    entry_type = fields.Selection([('Positive Adjusment', 'Positive Adjusment'),('Negative Adjusment', 'Negative Adjusment')], string='Entry Type')

    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity < 0:
                raise ValidationError(_("Quantity cannot be negative."))

    # SH
    sh_product_barcode_mobile = fields.Char(string="Mobile Barcode", store=True)
    # SH

    #barcode
    @api.onchange('sh_product_barcode_mobile')
    def _onchange_sh_product_barcode_mobile(self):
        if self.sh_product_barcode_mobile:
            self.parse_gs1_128_barcode(self.sh_product_barcode_mobile)

 
    def parse_gs1_128_barcode(self, barcode):
        barcode_2 = barcode
        if barcode_2[:2] == "01":
            digit_first_14 = barcode_2[2:16] 
            digit_2 = barcode_2[:2]
        else:
            digit_2 = ''
            digit_first_14 = barcode_2

        if digit_first_14:
            item_barcodes = self.env['tms.item.identifiers'].search([
                ('sh_product_barcode_mobile','=', digit_first_14),
            ])
            if item_barcodes:
                self.item_no = item_barcodes.item_no.id

        barcode_2 = barcode_2.replace(digit_2+digit_first_14, '')


        if barcode_2:
            identifier_obj = self.env['tms.item.identifiers'].search([('item_no', '=', self.item_no.id), ('sh_product_barcode_mobile', '=', digit_first_14)], limit=1) # digit_2+
        
            while barcode_2:
                if identifier_obj:
                    iden_line = self.env['tms.item.identifiers.line'].search([
                        ('header_id', '=', identifier_obj.id),
                    ],order="sequence asc")
                    if not iden_line:
                        break

                    for line in iden_line:
                        digit_first_2 = barcode_2[:2]
                        if digit_first_2 == line.gs1_identifier:
                            barcode_3 = barcode_2[2:line.data_length]
                            if digit_first_2 == '10' or digit_first_2 == '23': #lot  
                                self.lot_number = barcode_3
                            elif digit_first_2== '21': #sn
                                self.serial_number = barcode_3
                            elif digit_first_2 == '17':
                                self.exp_date = self.parse_exp_date(barcode_3)
                            elif digit_first_2 == '30':
                                self.quantity = int(barcode_3)

                            barcode_2 = barcode_2.replace(digit_first_2+barcode_3, '')
                        else:
                            barcode_2 = ''
            self.fnCheckSNLOTArray(self.serial_number,self.lot_number)

    def fnCheckSNLOTArray(self, sn, lot):
        reserarray = self.reservation_entry_ids
       
        if sn and lot :
            for rsn in reserarray :
                if rsn.serial_no == sn :
                    raise UserError(f'SN Number has {sn} been used in Lines')
        elif sn:
            for rsn in reserarray :
                if rsn.serial_no == sn :
                    raise UserError(f'SN Number has {sn} been used in Lines')
        elif lot:
             for rsn in reserarray :
                if rsn.lot_no == lot :
                    raise UserError(f'Lot Number has {lot} been used in Lines')
            
    def parse_exp_date(self, date_str):
        """Parse expiration date from barcode to a date object (assuming YYMMDD format)."""
        try:
            exp_date = datetime.strptime(date_str, '%d%m%y').date()
            return exp_date
        except ValueError:
            raise ValidationError("Invalid expiration date format in barcode.")

    #barcode
    @api.depends('item_tracking_code')
    def _compute_contains_sn(self):
        for record in self:
            record.contains_sn = 'SN' == self.fnCheckTrackingCode("SN")
    
    @api.depends('item_tracking_code')
    def _compute_contains_lot(self):
        for record in self:
            record.contains_lot = 'LOT' == self.fnCheckTrackingCode("LOT")

    @api.depends('contains_lot', 'contains_sn')
    def _compute_contains_snlot(self):
        for record in self:
            if record.contains_lot and record.contains_sn:
                record.contains_lot_sn = True
    
    def fnCheckTrackingCode(self,cekApa) :
        if cekApa == "SN" :
            if self.item_no.sn_specific_tracking  or self.item_no.sn_purchase_inbound_tracking:
                return 'SN'
        elif cekApa == 'LOT' :
            if self.item_no.lot_specific_tracking or self.item_no.lot_purchase_inbound_tracking:
                return 'LOT'
    

    @api.depends('handheld_transaction_id')
    def _compute_available_item_ids(self):
        """
        Domain Item. Get Item from Purchase Order
        """
        #for record in self:
        if self.handheld_transaction_id:
            source_doc,source_line,default_item_uom = self.fnGetLinkToSourceLine(self.handheld_transaction_id.document_type)
            if source_doc and source_doc != "8":
                source_line_map = source_line.mapped('no.id')
                self.available_item_ids = [(6, 0, source_line_map)]
            elif source_doc and source_doc == "8" :
                source_line_map = source_line.mapped('id')
                self.available_item_ids = [(6, 0, source_line_map)]
            else :
                self.available_item_ids = [(5, 0, 0)]
        else:
            self.available_item_ids = [(5, 0, 0)]
                
                
    @api.onchange('item_no')
    def _onchange_item_no(self):
        """
        Auto fill Description onchange item no
        """ 
        if self.item_no and self.handheld_transaction_id:
            self._check_first_line_detail()
            self.handheld_document_type = self.handheld_transaction_id.document_type
            source_doc,source_line,default_item_uom = self.fnGetLinkToSourceLine(self.handheld_transaction_id.document_type)
            if source_doc and source_doc != "8":
                source_line_map = source_line.filtered(
                        lambda line: line.no.id == self.item_no.id
                )
                if source_line_map:
                    line = source_line_map[0]
                    self.item_description = line.description
                    self.item_no_no = self.item_no.no

                    if self.handheld_transaction_id.document_type in ["1","2"] :
                        self.line_po = line.id
                    elif  self.handheld_transaction_id.document_type in ["3","4"] :
                        self.line_so = line.id
                    elif  self.handheld_transaction_id.document_type in ["5","6"] :
                        self.line_to = line.id
            elif source_doc and source_doc == "8":
                self.item_no_no = self.item_no.no

            self.source_doc_no = self.handheld_transaction_id.source_doc_no


    @api.onchange('line_po','line_so','line_to')
    def _onchange_line_posoto(self):
        if self.item_no and self.handheld_transaction_id:
            source_doc,source_line,default_item_uom = self.fnGetLinkToSourceLine(self.handheld_transaction_id.document_type)
          
            if source_doc and source_doc != "8":
                source_line_map = source_line.filtered(
                    lambda line: line.no.id == self.item_no.id
                )

                if source_line_map:
                    self.item_uom = default_item_uom.id
        
    def clear_value(self):
        """
        Clear the value of specific fields.
        """
        self.item_no = False
        self.item_description = False
        self.quantity = False
        self.barcode_code = False
        self.reservation_entry_ids = [(5, 0, 0)]  # Clear the One2many field
        self.sh_product_barcode_mobile = ''
        self.item_uom = False
        self.serial_number = ''
        self.lot_number = ''
        self.line_po = False
        self.line_so = False
        self.line_to = False
    
    # V2
    def submit_scan_line(self):
        self.ensure_one()

        if not self.item_no or not self.handheld_transaction_id:
            raise UserError('Item No. must be selected.')

        if self.item_no.man_expir_date_entry_reqd and self.item_no.strict_expiration_posting:
            for entry in self.reservation_entry_ids:
                if not entry.expiration_date:
                    raise ValidationError('Expiration Date is required for item %s due to its expiration settings.' % self.item_no.no)

        source_line = self.fnCheckSourceDoc(self.handheld_transaction_id.document_type)

        #update ke transaction line - quantity to receive
        #if not self.reservation_entry_ids:
        #    qty_to_receive = self.quantity
        #else:
        #    qty_to_receive = sum(entry.quantity for entry in self.reservation_entry_ids)

        #qty transaction line
        #quantity = source_line[0].quantity if source_line else 0.0      

        checksn = False
        if self.contains_sn or self.contains_lot or self.contains_lot_sn :
            checksn = True
     
        if checksn == False:
            self.fnInsertToTransactionWithoutSN()
        else:
            self.fnInsertToTransactionWithSN()
          

        empty_source_entries = self.env['tms.reservation.entry'].search([
            ('source_id', '=', False)
        ])

        empty_source_entries.unlink()

        self.clear_value()

    def fnInsertToTransactionWithoutSN(self) :
        line = self.fngetLineNo(self.handheld_transaction_id.document_type) 
        ln = 10000
        if self.handheld_transaction_id.document_type != "8":
            receipt_line = self.env['tms.handheld.transaction.line'].search([
                ('handheld_transaction_id', '=', self.handheld_transaction_id.id),
                ('item_no', '=', self.item_no.id),
                ('line_no', '=', line.line_no),
                ('item_uom', '=', self.item_uom.id)
            ],order="line_no desc",limit = 1)

            if receipt_line :
                ln = receipt_line.line_no
            else :
                ln = line.line_no
            
        elif self.handheld_transaction_id.document_type == "8" : 
            receipt_line = self.env['tms.handheld.transaction.line'].search([('handheld_transaction_id', '=', self.handheld_transaction_id.id),
            ('item_no', '=', self.item_no.id),('item_uom', '=', self.item_uom.id)
            ],order="line_no desc",limit = 1)
          
            if receipt_line :
                ln = receipt_line.line_no 
            else : 
                receipt_line2 = self.env['tms.handheld.transaction.line'].search([('handheld_transaction_id', '=', self.handheld_transaction_id.id)],order="line_no desc",limit = 1)
                ln = receipt_line2.line_no + 10000
            
                
        if receipt_line :
            receipt_line.qty_to_receive += self.quantity
        else:
            iuom = False
            iuom = self.item_uom.id

            if iuom == False:
                raise UserError(f'Unit of Measure Code required for this operation cannot found in Item Unit of Measure. Item No. = {self.item_no.no}, Code={self.item_no.base_unit_of_measure_id}.')

            receipt_line.create({
                'handheld_transaction_id': self.handheld_transaction_id.id,
                'item_no': self.item_no.id,
                'description': self.item_no.description,
                'quantity': self.quantity,
                'item_uom': iuom,
                'qty_to_receive': self.quantity,
                'line_no': ln,
                'entry_type': self.entry_type if self.entry_type else False,
            })

    def fnInsertToTransactionWithSN(self) :
        res_source_entries = self.env['tms.reservation.entry'].search([
            ('source_id', '=', False),('purchase_scan_id','=',self.id),
        ])
        
        for entry in res_source_entries:
            
            item = self.env['tms.item'].search([
                    ('no','=',entry.item_no)
                ])
            iuom = False
            item_uom = self.item_uom.search([
                ('code', '=', item.base_unit_of_measure_id),
                ('item_no', '=', item.no)
            ])
            iuom = item_uom.id

            if iuom == False:
                raise UserError(f'Unit of Measure Code required for this operation cannot found in Item Unit of Measure. Item No. = {item.no}, Code={item.base_unit_of_measure_id}.')

            if self.handheld_transaction_id.document_type != "8":
                receipt_line = self.env['tms.handheld.transaction.line'].search([
                    ('handheld_transaction_id', '=', self.handheld_transaction_id.id),
                    ('item_no', '=', entry.item_no),
                    ('line_no', '=', entry.line_no),
                    ('item_uom', '=', iuom),
                ],order="line_no desc",limit = 1)
                if receipt_line :
                    ln = receipt_line.line_no
                else :
                    ln = entry.line_no
               
            elif self.handheld_transaction_id.document_type == "8" : 
                receipt_line = self.env['tms.handheld.transaction.line'].search([('handheld_transaction_id', '=', self.handheld_transaction_id.id)
                ,('item_no', '=', entry.item_no),('item_uom', '=', iuom)
                ],order="line_no desc",limit = 1)
                
                if receipt_line :
                    ln = receipt_line.line_no 
                else : 
                    receipt_line2= self.env['tms.handheld.transaction.line'].search([('handheld_transaction_id', '=', self.handheld_transaction_id.id)],order="line_no desc",limit = 1)
                    
                    ln = receipt_line2.line_no + 10000

            
            if receipt_line : 
                self.sendhandheldsnLotForCheck(entry.serial_no,entry.lot_no,entry.line_no,receipt_line.id)
                receipt_line.qty_to_receive += entry.quantity
                                     
                self.env['tms.reservation.entry'].create({
                    'item_no': item.no,
                    'source_type': '39',  # Purchase Order
                    'quantity': 1 if self.contains_sn else entry.quantity,
                    'serial_no': entry.serial_no,
                    'expiration_date': entry.expiration_date,
                    'source_id': self.handheld_transaction_id.document_no,
                    'lot_no': entry.lot_no,
                    'line_id' : receipt_line.id,
                    'line_no': ln
                })
                
            else:
                rcpt_line = receipt_line.create({
                    'handheld_transaction_id': self.handheld_transaction_id.id,
                    'item_no': item.id,
                    'description': item.description,
                    'quantity': entry.quantity,
                    'item_uom': iuom,
                    'qty_to_receive': entry.quantity,
                    'line_no': ln,
                    'entry_type': self.entry_type if self.entry_type else False,
                })

                self.sendhandheldsnLotForCheck(entry.serial_no,entry.lot_no,entry.line_no,rcpt_line.id)
                
                self.env['tms.reservation.entry'].create({
                    'item_no': item.no,
                    'source_type': '39',  # Purchase Order
                    'quantity': 1 if self.contains_sn else entry.quantity,
                    'serial_no': entry.serial_no,
                    'expiration_date': entry.expiration_date,
                    'source_id': self.handheld_transaction_id.document_no,
                    'lot_no': entry.lot_no,
                    'line_id' : rcpt_line.id,
                    'line_no': ln
                })

    def fngetLineNo(self,doctype) :
        line = False
        if doctype in ["1","2"] :
            line = self.line_po
        elif doctype in ["3","4"] :
             line = self.line_so
        elif doctype in ["5","6"] :
             line = self.line_to
        
        
        return line

    def fnCheckSourceDoc(self,doctype) : 
        
        if doctype in ["1","2"] :
            tablename = "Purchase Order"
        elif doctype in ["3","4"] :
            tablename = "Sales Order"
        elif doctype in ["5","6"] :
            tablename = "Transfer Order"
        elif doctype in ["8"] :
            tablename = False

        source_doc,source_line,default_item_uom = self.fnGetLinkToSourceLine(doctype)

        if not source_doc and source_doc != "8":
            raise UserError('No matching {tablename} found.')
        
        linedoc = self.fngetLineNo(doctype) 

        if linedoc :
            source_line = source_line.filtered(
                lambda line: line.line_no == linedoc.line_no
            )
            
        if not source_line:
            raise UserError('No matching {tablename}  Line found for the selected item.')
        
        return source_line
    
    def fnGetLinkToSourceLine(self,doctype):
        
        if doctype in ["1","2"] :
            source_doc = self.env['tms.purchase.order.header'].search([
                ('no', '=', self.handheld_transaction_id.source_doc_no)
            ], limit=1)

            source_line = source_doc.purchase_order_line_ids
     
            default_item_uom = self.item_uom.search([
                    ('code', '=', self.line_po.unit_of_measure_code.code),
                    ('item_no', '=', self.line_po.no.no)
                ])

        elif doctype in ["3","4"] :
           
            source_doc = self.env['tms.sales.order.header'].search([
                ('no', '=', self.handheld_transaction_id.source_doc_no)
            ], limit=1)

            source_line = source_doc.sales_line_ids

            default_item_uom = self.item_uom.search([
                ('code', '=', self.line_so.unit_of_measure_code),
                ('item_no', '=', self.line_so.no.no)
            ])

        elif doctype in ["5","6"] :
           
            source_doc = self.env['tms.transfer.header'].search([
                ('no', '=', self.handheld_transaction_id.source_doc_no)
            ], limit=1)

            source_line = source_doc.transfer_line_ids

            default_item_uom = self.item_uom.search([
                ('code', '=', self.line_to.uom_code),
                ('item_no', '=', self.line_to.no.no)
            ])
            
        elif doctype in ["8"] :
            source_doc = "8"
            source_line = self.env["tms.item"].search([])
            default_item_uom = self.item_uom.search([('item_no', '=', self.item_no.no)])          
        return source_doc,source_line,default_item_uom
    
    # V2

    def sendhandheldsnLotForCheck(self,sn,lot,lineno,lineid):

        current_company = self.env.user.company_id
        url = f'http://{current_company.ip_or_url_api}:{current_company.port_api}/Thomasong/OData/Company(\'{current_company.name}\')/Handheld_SN_OData?$format=json'
        #url = f"http://192.168.1.5:9148/Thomasong/OData/Company('THOMASONG')/Handheld_SN_OData?$format=json"
        headers = {'Content-Type': 'application/json'}

        
        username = current_company.username_api
        password = current_company.password_api

        if username == False or password == False or  current_company.ip_or_url_api == False or current_company.port_api == False:
             raise ValidationError( f'You have to setup API Connection in companies')
        
        auth = HttpNtlmAuth(username, password)  # Using requests_ntlm2

        data_sn = {
            "Processed_Header_ID": str(self.handheld_transaction_id.id),
            "Line_ID": lineid,
            "Line_No": lineno,
            "Serial_No": sn if sn else "",
            "Lot_No": lot if lot else "",
            "Document_Type" : self.handheld_transaction_id.document_type
            #"Expired_Date": self.expiration_date.isoformat() if self.expiration_date else datetime.min.isoformat(),
            #"Quantity": str(self.quantity)
        }
        
        response = requests.post(url, headers=headers, auth=auth, json=data_sn)
        
        if response.status_code == 400 :
            response_json = response.json()
            resp = response_json.get('odata.error', {}).get('message', {}).get('value', response.text )
            raise ValidationError( f'Nav Error {resp}')
        

    def back_to_receipt(self):
        """
        Redirect the user back to the purchase receipt form view.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Receipt',
            'res_model': 'tms.handheld.transaction',
            'view_mode': 'form',
            'res_id': self.handheld_transaction_id.id,
            'target': 'main',
            'context': {
                'form_view_initial_mode': 'edit',
            }
        }

    @api.onchange('serial_number')
    def _onchange_serial_number(self):
        """
        Handle the Serial Number scan separately.
        Automatically set quantity to 1 and create a reservation entry.
        """
        if self.contains_sn == True and self.contains_lot ==False  :
            if self.serial_number:
                self._create_serial_reservation_entry(self.serial_number,self.lot_number)
                    
                self.serial_number = ''
                self.lot_number = ''
      

    @api.onchange('lot_number', 'quantity')
    def _onchange_lot_number(self):
        """
        Handle the Lot Number scan separately.
        The quantity will be based on user input.
        """
        if self.contains_sn == False and self.contains_lot ==True  :
            if self.lot_number and self.quantity > 0:
                self._create_serial_reservation_entry(self.serial_number,self.lot_number)
        elif self.contains_sn == True and self.contains_lot ==True  :
            if self.lot_number :
                self._create_serial_reservation_entry(self.serial_number,self.lot_number)
            self.serial_number = ''
            self.lot_number = ''

    def _create_serial_reservation_entry(self,sn,lot):
        self._check_first_line_detail()
        self.fnCheckSNLOTArray(sn,lot)
        if sn :
            existing_entry = self.reservation_entry_ids.filtered(
                lambda r: r.serial_no == self.serial_number
            )
        elif lot :
            existing_entry = self.reservation_entry_ids.filtered(
                lambda r: r.lot_no == self.lot_number
            )

        # Add new reservation entry for serial number temporary
        linedoc = self.fngetLineNo(self.handheld_transaction_id.document_type) 

        if linedoc :
            ln = linedoc.line_no
        else :
            ln =10000

        self.reservation_entry_ids = [(0, 0, {
            'lot_no': self.lot_number,
            'serial_no': self.serial_number,
            'quantity': 1 if sn else self.quantity,  # Default quantity is 1 for serial number
            'purchase_scan_id': self.id,
            'expiration_date': self.exp_date if self.exp_date else False,
            'source_type': '39',
            'item_no': self.item_no.no,
            'line_no': ln
         
        })]

        self.lot_number = ''  # Clear after adding
        self.quantity = ''
        self.barcode_code = ''
        self.exp_date = ''
        self.sh_product_barcode_mobile = ''
       


    def _check_first_line_detail(self):
        """
        Check if the first line of reservation_entry_ids has a serial number filled.
        """
        first_entry = self.reservation_entry_ids[:1]  # Get the first entry
        if first_entry and first_entry.item_no !=  self.item_no.no :
                raise UserError('You have to finished this operation before scan another item.')               
      
         
      
                 
               
             
        

    