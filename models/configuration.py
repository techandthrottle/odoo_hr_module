#-*- coding: utf-8 -*-

from odoo import models, fields, api, _


class WageTypeConfiguration(models.Model):
    _name = 'hr_china.wage_type'

    @api.onchange('wage_type', 'days')
    def generate_wage_name(self):
        if self.wage_type == 'monthly':
            self.name = self.wage_type.capitalize() + ' (' + str(self.days) + ')'
        else:
            self.name = self.wage_type.capitalize()

    name = fields.Char(string='Name', computed=generate_wage_name)
    wage_type = fields.Selection([('monthly', 'Monthly'), ('hourly', 'Hourly')], string='Type', required=True)
    days = fields.Integer(string='Days (In a month)', default=30)
    formula = fields.Char(string='Formula')


class PaymentMethodConfiguration(models.Model):
    _name = 'hr_china.payment_method'

    name = fields.Char(string='Name')


class CompanyNameLogoConfig(models.Model):
    _name = 'hr_china.company_name_logo'

    name = fields.Char(string='Company Name')
    logo = fields.Binary(string='Company Logo')
    is_active = fields.Boolean(string='Active', default=False)


class LeaveConfiguration(models.Model):
    _name = 'hr_china.leave_config'

    name = fields.Char(string='Name')
    days_allowed = fields.Integer(string='Days Allowed')
    leave_type = fields.Selection([('paid', 'Paid'), ('unpaid', 'Unpaid')], string='Type')
