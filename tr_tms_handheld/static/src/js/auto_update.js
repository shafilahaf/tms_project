odoo.define('tr_tms_handheld.barcode_focus', function(require) {
    "use strict";

    var FormController = require('web.FormController');
    var core = require('web.core');

    FormController.include({
        start: function() {
            this._super.apply(this, arguments);
            this._setupBarcodeListener();
        },

        _setupBarcodeListener: function() {
            var self = this;
            this.$el.on('input', 'input[name="sn_or_lotno"]', function(event) {
                var $barcodeField = $(event.currentTarget);
                clearTimeout(self.barcodeTimeout);
                self.barcodeTimeout = setTimeout(function() {
                    self._processBarcode($barcodeField.val());
                }, 500);
            });
        },

        _processBarcode: function(barcode) {
            var self = this;
            if (barcode) {
                self._rpc({
                    model: 'tms.purchase.scan.item',
                    method: 'insert_sn_or_lotno',
                    args: [self.model.localData[self.handle].res_id, barcode],
                }).then(function () {
                    // Save the record without reloading
                    self.saveRecord().then(function() {
                        // Clear the barcode field after save
                        self.$el.find('input[name="sn_or_lotno"]').val(''); 

                        // Update the specific field
                        self.trigger_up('field_changed', {
                            dataPointID: self.handle,
                            fieldName: 'reservation_entry_ids',
                        });

                        // Trigger updates for other fields if needed
                        self.trigger_up('field_changed', {
                            dataPointID: self.handle,
                            fieldName: 'purchase_receipt_id',
                        });
                        self.trigger_up('field_changed', {
                            dataPointID: self.handle,
                            fieldName: 'item_no',
                        });
                        self.trigger_up('field_changed', {
                            dataPointID: self.handle,
                            fieldName: 'item_description',
                        });
                        self.trigger_up('field_changed', {
                            dataPointID: self.handle,
                            fieldName: 'quantity',
                        });

                    }).catch(function (error) {
                        console.log("Save failed: ", error);
                    });
                }).catch(function (error) {
                    console.log("Barcode processing failed: ", error);
                });
            }
        }
    });
});
