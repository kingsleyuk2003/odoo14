
odoo.kin_stock = function(instance, local) {



    local.alert_stock = instance.Widget.extend({ // The client action handler
           start: function() {
               alert('Here Na');
               return this._super();
            },
        });
//see reference: https://www.odoo.com/forum/help-1/question/how-to-refresh-the-original-view-after-wizard-actions-10268  from Petar
//      instance.web.ActionManager = instance.web.ActionManager.extend({
//        //overriding an existing function
//        ir_actions_acts_lose_wizard_and_reload_view: function (action, options) {
//            if (!this.dialog) {
//                options.on_close();
//            }
//            this.dialog_stop();
//            this.inner_widget.views[this.inner_widget.active_view].controller.reload();
//            return $.when();
//        },
//    });

instance.web.client_actions.add('action_client_kin_stock_tag', 'instance.kin_stock.alert_stock'); // mapping the widget to the client action


}