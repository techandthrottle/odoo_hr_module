odoo.define('hr_china.edit_btn', function (require) {
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
            if(this.dataset.model == 'hr_china.timesheet'){
                var create_btn = this.$buttons.find('.o_list_button_add');
                create_btn.hide();
            }
            if (this.$buttons){
                var btn = this.$buttons.find('button.hr_china_timesheet_create')
                btn.on('click', this.proxy('hr_china_timesheet_create'))
            }
            if(this.dataset.model == 'hr_china.payslip'){
                var create_btn1 = this.$buttons.find('.o_list_button_add');
                var import_btn1 = this.$buttons.find('.o_button_import');
                create_btn1.hide();
                import_btn1.hide();
            }
            if (this.$buttons){
                var btn = this.$buttons.find('button.hr_china_payslip_create')
                btn.on('click', this.proxy('hr_china_payslip_create'))
            }
        },
        hr_china_timesheet_create: function() {
            var self = this
            var context = this.dataset._model;
            new Model('hr_china.timesheet.create')
                .call('do_get_display', [], {context: context})
                .then(function(response) {
                    self.do_action(response);
                });
        },
        hr_china_payslip_create: function() {
            var self = this
            var context = this.dataset._model;
            new Model('hr_china.payslip.create')
                .call('display_wizard', [], {context: context})
                .then(function(response) {
                    self.do_action(response);
                });
        }
    });

    FormView.include({
        load_record: function(record) {
            if (record) {
                var self = this;
                if (this.model == 'hr_china.leaves') {
                    var edit_btn = self.$buttons.find('.o_form_button_edit');
                    if (record.state == 'confirm' || record.state == 'validate' || record.state == 'refuse'){
                        edit_btn.hide();
                    } else {
                        edit_btn.show();
                    }
                }
            }
            return this._super(record);
        }
    });
});