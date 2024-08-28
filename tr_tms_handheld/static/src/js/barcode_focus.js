// Focus
// odoo.define('tr_tms_handheld.barcode_focus', function(require) {
//     "use strict";
//     var core = require('web.core');
//     var FormController = require('web.FormController');

//     FormController.include({
//         _onFieldChanged: function(event) {
//             this._super.apply(this, arguments);
//             if (event.data.changes.barcode !== undefined) {
//                 var $barcodeField = this.$el.find('input[name="barcode"]');
//                 $barcodeField.focus();
//             }
//         }
//     });
// });

// Continuous Scan
odoo.define('tr_tms_handheld.barcode_focus', function(require) {
    "use strict";

    var FormController = require('web.FormController');

    FormController.include({
        start: function() {
            this._super.apply(this, arguments);
            this._setupBarcodeListener();
        },

        _setupBarcodeListener: function() {
            var self = this;
            this.$el.on('input', 'input[name="barcode"]', function(event) {
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
                    model: 'tms.receipt.detail.header',
                    method: 'process_barcode',
                    args: [[self.model.localData[self.handle].res_id], barcode],
                }).then(function () {
                    self.$el.find('input[name="barcode"]').val(''); // Clear the barcode field
                    self.reload(); // Reload the form to update the lines
                }).catch(function (error) {
                    console.log(error);
                });
            }
        }
    });
});

// dianadi021 test Code
// Enter Key
// odoo.define("tr_tms_handheld.barcode_focus", function (require) {
// 	"use strict";

// 	var FormController = require("web.FormController");

// 	FormController.include({
// 		events: _.extend({}, FormController.prototype.events, {
// 			'keyup input[name="barcode"]': "_onHeaderFieldKeyup",
// 		}),

// 		start: function () {
// 			this._super.apply(this, arguments);
// 			this._onHeaderFieldKeyup();
// 		},

// 		_onHeaderFieldKeyup: function (event) {
// 			if (event && event.key === "Enter") {
// 				event.preventDefault();
// 				var $input = $(event.target);
// 				var barcode = $input.val();

// 				if (!barcode) {
// 					alert("Field Barcode is Empty");
// 				}
				
// 				setTimeout(async () => {
// 					await this._addToLine(barcode);
// 				}, 1000);
// 				$input.val("");
// 			}
// 		},

// 		_addToLine: async function (barcode) {
// 			if (barcode) {
// 				await this._rpc({
// 					model: "tms.receipt.detail.header",
// 					method: "process_barcode",
// 					args: [[this.model.localData[this.handle].res_id], barcode],
// 				});

// 				setTimeout(async () => {
// 					await this._rpc({
// 						model: "tms.receipt.detail.header",
// 						method: "submit_receipt_detail",
// 					});
// 				}, 500);

// 				this.reload();
// 			}
// 		},
// 	});
// });

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
