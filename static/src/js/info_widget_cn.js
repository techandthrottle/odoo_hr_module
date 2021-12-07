odoo.define('hr_china.info_widget', function (require) {
"use strict";

    var core = require('web.core');
    var form_common = require('web.form_common');
    var formats = require('web.formats');
    var Model = require('web.Model');

    var QWeb = core.qweb;
    var _t = core._t;

    var ShowInfoWidgetHRCN = form_common.AbstractField.extend({
        render_value: function() {
            var self = this;
            var info = this.get('value');
            var rand_id = parseInt(Math.random() * 100000);
            var msg = this.options.text;
            this.$el.html(QWeb.render('ShowInfoWidget', {
                'rand_id': rand_id,
            }));
            _.each(this.$('.js_popout_info'), function(k, v){
                var options = {
                    'content': QWeb.render('ShowInfoPopupWidget', {
                        'message': msg,
                    }),
                    'html': true,
                    'placement': 'right',
                    'title': _t('Information'),
                    'trigger': 'focus',
                    'delay': { "show": 0, "hide": 100 },
                };
                $(k).popover(options);
            });
        },

        _toggle_label: function() {
            var empty = this.get('effective_readonly') && !this.is_set();
            this.$label.toggleClass('o_form_label_empty', empty).toggleClass('o_form_label_false', this.get('effective_readonly') && this.get('value') === false);
        }
    });

    core.form_widget_registry.add('show_info_hr_cn', ShowInfoWidgetHRCN);
});