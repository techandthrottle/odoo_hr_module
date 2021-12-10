odoo.define('hr_china.alter_create', function (require) {
    var FormView = require('web.FormView');
    var core = require('web.core');
    var Column = core.list_widget_registry.get('field');
    var Model = require('web.DataModel');
    var session = require('web.session');
    var ListView = require('web.ListView');
    var data = require('web.data');
    var QWeb = core.qweb;

    ListView.include({
        render_buttons: function() {
            this._super.apply(this, arguments);
            if(this.dataset.model == 'hr_china.payslip_summary') {
                var create_btn = this.$buttons.find('.o_list_button_add')
                var import_btn = this.$buttons.find('.o_button_import')
                create_btn.hide();
                import_btn.hide();
            }
            if (this.$buttons){
                var btn = this.$buttons.find('button.hr_china_payslip_summary')
                btn.on('click', this.proxy('hr_china_summary_create'))
            }
        },
        hr_china_summary_create: function() {
            var self = this
            var context = this.dataset._model;
            new Model('hr_china.payslip_summary.wiz')
                .call('display_wizard', [], {})
                .then(function(response) {
                    self.do_action(response);
                });
        }
    });

    FormView.include({
        remove_buttons: function() {
            this._super.apply(this, arguments);
            if(this.dataset.model == 'hr_china.payslip_summary') {
                var edit_btn = this.$buttons.find('.o_form_button_edit')
                var create_frm_btn = this.$buttons.find('.o_form_button_create')
                edit_btn.hide();
                create_frm_btn.hide();
            }
        }
    });
});