odoo.define('tr_tms_handheld.tree_button_transaction', function (require) {
    "use strict";
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var TreeButton = ListController.extend({
       buttons_template: 'tr_tms_handheld.buttontransaction',
       events: _.extend({}, ListController.prototype.events, {
           'click .open_wizard_action': '_OpenWizard',
       }),
       _OpenWizard: function () {
           var self = this;
            this.do_action({
               type: 'ir.actions.act_window',
               res_model: 'tms.handheld.transaction',
               name :'Transaction',
               view_mode: 'form',
               view_type: 'form',
               views: [[false, 'form']],
               target: 'current',
               res_id: false,
               context: {
                'default_document_type': '8'
                }
           });
       }
    });
    var KPIListView = ListView.extend({
       config: _.extend({}, ListView.prototype.config, {
           Controller: TreeButton,
       }),
    });
    viewRegistry.add('button_in_tree_transaction', KPIListView);
    });
    