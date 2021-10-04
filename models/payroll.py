# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta, date, time
from odoo.exceptions import UserError, AccessError, ValidationError

from pprint import pprint


class HRChinaPayroll(models.Model):
    _name = 'hr_china.payslip'

    @api.multi
    def _get_timesheet_name(self):
        for item in self:
            item.name = item.employee_id.name + ' Payslips' if item.employee_id else ''

    @api.multi
    def _get_wage_type(self):
        for item in self:
            item.wage_type = item.employee_id.c_wage_type if item.employee_id else ''

    employee_id = fields.Many2one('hr.employee', string='Employee')
    name = fields.Char(string='Name', compute=_get_timesheet_name)
    wage_type = fields.Selection([('monthly', 'Monthly'), ('hourly', 'Hourly')], string='Type')
    timesheet_id = fields.Many2one('hr_china.timesheet', string='Timesheet')
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    total_days = fields.Float(string='Total Days')
    worked_days = fields.Float(string='Worked Days')
    work_hours = fields.Float(string='Hours Worked')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('validate', 'Approved')],
                             string='Status', default='draft')

    @api.multi
    def _get_timesheet_state(self):
        for item in self:
            ret_val, color = 'Unknown', 'black'
            state = item.state
            if state == 'draft':
                ret_val = 'Draft'
                color = '#666666'
            elif state == 'confirm':
                ret_val = 'Confirmed'
                color = '#156bf4'
            elif state == 'validate':
                ret_val = 'Approved'
                color = '#5EBE6A'
            item.payslip_state = '<span class="item_badge" style="background-color:%s;">%s</span>' % (color, ret_val)

    payslip_state = fields.Html(string='Status', compute=_get_timesheet_state)
    overtime_hours = fields.Float(string='Overtime Hours')
    weekend = fields.Float(string='Weekend') #Copied from timesheet
    holiday = fields.Float(string='Holiday') #Copied from timesheet
    leave = fields.Float(string='Leaves') #Copied from Timsheet
    basic_pay = fields.Float(string='Basic Pay', compute='_get_basic_pay')
    total_hourly_pay = fields.Float(string='Total Hourly Pay', compute='_get_hourly_pay')
    overtime_pay = fields.Float(string='Overtime Pay')
    holiday_pay = fields.Float(string='Holiday Pay', compute='_get_holiday_pay')
    weekend_pay = fields.Float(string='Weekend Pay', compute='_get_weekend_pay')
    regular_days = fields.Integer(string='Regular Days')

    benefits_id = fields.Many2many('hr_china.benefits', string='Benefits')
    deductions_id = fields.Many2many('hr_china.deductions', string='Deductions')
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_get_emp_currency')
    gross_pay = fields.Float(string='Gross Pay', compute='_get_gross_pay')

    net_pay = fields.Float(string='Net Pay', compute='_get_net_pay')

    total_benefits = fields.Float(string='Total Benefits', store=True, compute='sum_benefits')
    total_deductions = fields.Float(string='Total Deduction', compute='get_sum_deductions')

    # payslip_benefits = fields.One2many('hr_china.payslip.benefits', 'payslip_id')
    # payslip_deductions = fields.One2many('hr_china.payslip.deductions', 'payslip_id')

    @api.onchange('benefits_id')
    def sum_benefits(self):
        for benefits in self:
            total_benefits = False
            for line in benefits.benefits_id:
                total_benefits = total_benefits + line.amount
            benefits.total_benefits = total_benefits

    @api.onchange('deductions_id')
    def get_sum_deductions(self):
        for item in self:
            total_ded = False
            for line in item.deductions_id:
                total_ded = total_ded + line.amount
            item.total_deductions = total_ded

    # @api.onchange('deductions_id')
    # def get_deductions(self):
    #     for deductions in self:
    #         total_deductions = False
    #         for line in deductions.deductions_id:
    #             total_deductions = total_deductions + line.amount
    #         deductions.total_deductions = total_deductions

    @api.multi
    def get_emp_name_str(self):
        for emp in self:
            emp.emp_name = emp.employee_id.name

    @api.multi
    def get_emp_pos_str(self):
        for emp in self:
            emp.emp_position = emp.employee_id.job_new_id.name

    emp_name = fields.Char(compute=get_emp_name_str)
    emp_position = fields.Char(compute=get_emp_pos_str)

    @api.onchange('employee_id')
    def _get_emp_currency(self):
        for item in self:
            item.currency_id = item.employee_id.currency_id.id

    @api.onchange('employee_id')
    def _get_hourly_pay(self):
        for item in self:
            item.total_hourly_pay = item.employee_id.c_hourly_rate * item.work_hours

    @api.onchange('employee_id')
    def _get_basic_pay(self):
        for item in self:
            mf = item.employee_id.c_monthly_fee
            wd = item.worked_days if item.worked_days else 1
            dim = item.regular_days if item.regular_days else 1
            item.basic_pay = (mf / dim) * wd

    @api.onchange('employee_id')
    def _get_holiday_pay(self):
        pass

    @api.onchange('employee_id')
    def _get_weekend_pay(self):
        for item in self:
            wk_pay = item.employee_id.c_weekends_fee if item.employee_id.c_weekends_fee else 0
            item.weekend_pay = wk_pay * item.weekend

    @api.onchange('employee_id', 'total_benefits')
    def _get_gross_pay(self):
        for item in self:
            benefits = item.benefits_id
            total = False
            for line in benefits:
                total = total + line.amount
            if item.wage_type == 'monthly':
                item.gross_pay = total + item.basic_pay + item.holiday_pay + item.weekend_pay
            else:
                item.gross_pay = total + item.total_hourly_pay + item.holiday_pay + item.weekend_pay

    @api.onchange('gross_pay', 'total_deductions')
    def _get_net_pay(self):
        for item in self:
            item.net_pay = item.gross_pay - item.total_deductions

    def print_payslip_form(self):
        payslip_id = str(self.id)
        payslip_name = self.name

        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/hr_china.payslip_form/%s?filename=%s' % (payslip_id, payslip_name),
            'target': 'new'
        }


class HRChinaPayslipBenefits(models.Model):
    _name = 'hr_china.payslip.benefits'

    payslip_id = fields.Many2one('hr_china.payslip', string='Payslip')
    benefits_id = fields.Many2one('hr_china.benefits', string='Benefits')
    amount = fields.Float(string='Amount')
    currency = fields.Many2one('res.currency', string='Currency')


class HRChinaPayslipDeductions(models.Model):
    _name = 'hr_china.payslip.deductions'

    payslip_id = fields.Many2one('hr_china.payslip', string='Payslip')
    deductions_id = fields.Many2one('hr_china.deductions', string='Deductions')
    amount = fields.Float(string='Amount')
    currency = fields.Many2one('res.currency', string='Currency')


class HRChinaPayrollCreate(models.TransientModel):
    _name = 'hr_china.payslip.create'

    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')

    @api.model
    def display_wizard(self):

        self.env['hr_china.payslip.create'].search([]).unlink()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr_china.payslip.create',
            'name': 'Payslips',
            'views': [(False, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }

    @api.multi
    def display_timesheet_wizard(self):
        self.env['hr_china.payslip.create_temp'].search([]).unlink()
        self.env['hr_china.payslip.ttt'].search([]).unlink()
        time_list = self.env['hr_china.timesheet'].search(['|', '|', ('period_from', '>=', self.start_date),
                                                                     ('period_to', '<=', self.start_date),
                                                                     ('period_from', '>=', self.end_date),
                                                                     ('period_to', '<=', self.end_date)])

        for item in time_list:
            trans_data = {
                'timesheet_id': item.id,
                'employee_id': item.employee_id.id,
                'period_from': item.period_from,
                'period_to': item.period_to,
                'work_hours': item.work_time,
                'overtime_hours': item.overtime_hours,
                'weekend': item.weekend,
                'holiday': item.holiday,
                'leave': item.leaves,
                'working_days': item.total_days,
                'wage_type': item.contract_type,
                'name': item.employee_id.name,
                'regular_days': item.regular_days
            }
            self.env['hr_china.payslip.ttt'].create(trans_data)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr_china.payslip.create_temp',
            'name': 'Payslips',
            'views': [(False, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }


class HRChinaPayrollTimesheetTempTrans(models.TransientModel):
    _name = 'hr_china.payslip.ttt'

    timesheet_id = fields.Many2one('hr_china.timesheet')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    job_title_id = fields.Many2one('hr_china.job_titles', string='Position')
    period_from = fields.Datetime(string='Payslip Period From')
    period_to = fields.Datetime(string='Payslip Period To')
    regular_days = fields.Integer(string='Regular Days')
    overtime_hours = fields.Float(string='Overtime Hours')
    weekend = fields.Float(string='Weekends')
    holiday = fields.Float(string='Holidays')
    leave = fields.Float(string='Leaves')
    working_days = fields.Float(string='Working Days') #TOTAL DAYS EQUIVALENT
    work_hours = fields.Float(string='Work Hours') #WORK TIME EQUIVALENT
    wage_type = fields.Selection([('monthly', 'Monthly'), ('hourly', 'Hourly')], string='Type')
    name = fields.Char()


class HRChinaPayrollCreateTemp(models.TransientModel):
    _name = 'hr_china.payslip.create_temp'

    my_id = fields.Many2many('hr_china.payslip.ttt', onedelete='cascade')
    timesheet_id = fields.Many2one('hr_china.timesheet')
    employee_id = fields.Many2one('hr.employee')
    department_id = fields.Many2one('hr.department', string='Department')
    job_title_id = fields.Many2one('hr_china.job_titles', string='Position')
    period_from = fields.Datetime(string='Payslip Period From')
    period_to = fields.Datetime(string='Payslip Period To')
    work_hours = fields.Float(string='Work Hours')
    overtime_hours = fields.Float(string='Overtime Hours')
    weekend = fields.Float(string='Weekends')
    holiday = fields.Float(string='Holidays')
    leave = fields.Float(string='Leaves')
    working_days = fields.Float(string='Working Days')
    regular_days = fields.Integer(string='Regular Days')
    wage_type = fields.Selection([('monthly', 'Monthly'), ('hourly', 'Hourly')],
                                 string='Type')

    # def _update_timesheet_id(self):
    #     self.ensure_one()
    #     for item in self:
    #         item.timesheet_id = item.my_id[0].timesheet_id.id
    #
    # @api.onchange('timesheet_id')
    # def _update_employee_id(self):
    #     for item in self:
    #         pprint("###########################")
    #         pprint(item.my_id)
    #         item.employee_id = item.my_id[0].employee_id.id
    #         count = 0
    #         if len(item.my_id) > 1:
    #             if count > 0:
    #                 for mi in item.my_id:
    #                     new_temp = self.env['hr_china.payslip.create_temp'].create({})
    #                     new_temp.my_id.create({})
    #                     new_temp.close_dialog()
    #             count += 1
    #
    # @api.onchange('timesheet_id')
    # def _update_department_id(self):
    #     self.ensure_one()
    #     for item in self:
    #         item.department_id = item.my_id.department_id.id
    #
    # @api.onchange('timesheet_id')
    # def _update_job_title(self):
    #     for item in self:
    #         item.job_title_id = item.my_id.job_title_id.id
    #
    # @api.onchange('timesheet_id')
    # def _update_period_from(self):
    #     for item in self:
    #         item.period_from = item.my_id.period_from
    #
    # @api.onchange('timesheet_id')
    # def _update_period_to(self):
    #     for item in self:
    #         item.period_to = item.my_id.period_to
    #
    # @api.onchange('timesheet_id')
    # def _update_work_hours(self):
    #     for item in self:
    #         item.work_hours = item.my_id.work_hours
    #
    # @api.onchange('timesheet_id')
    # def _update_overtime_hours(self):
    #     for item in self:
    #         item.overtime_hours = item.my_id.overtime_hours
    #
    # @api.onchange('timesheet_id')
    # def _update_holiday(self):
    #     for item in self:
    #         item.holiday = item.my_id.holiday
    #
    # @api.onchange('timesheet_id')
    # def _update_weekend(self):
    #     for item in self:
    #         item.weekend = item.my_id.weekend
    #
    # @api.onchange('timesheet_id')
    # def _update_leave(self):
    #     for item in self:
    #         item.leave = item.my_id.leave
    #
    # @api.onchange('timesheet_id')
    # def _update_working_days(self):
    #     for item in self:
    #         item.working_days = item.my_id.working_days
    #
    # @api.onchange('timesheet_id')
    # def _update_regular_days(self):
    #     for item in self:
    #         item.regular_days = item.my_id.regular_days
    #
    # @api.onchange('timesheet_id')
    # def _update_wage_type(self):
    #     for item in self:
    #         item.wage_type = item.my_id.wage_type

    # @api.model
    # def create(self, vals):
    #     if 'my_id' in vals:
    #         temp_ids = vals['my_id'][0][2]
    #         for tid in temp_ids:
    #             ttt = self.env['hr_china.payslip.ttt'].search([('id', '=', tid)])
    #             trans_data = {
    #                 'timesheet_id': ttt.timesheet_id.id,
    #                 'employee_id': ttt.employee_id.id,
    #                 'start_date': ttt.period_from,
    #                 'end_date': ttt.period_to,
    #                 'wage_type': ttt.wage_type,
    #                 'worked_days': ttt.working_days,
    #                 'work_hours': ttt.work_hours,
    #                 'overtime_hours': ttt.overtime_hours,
    #                 'weekend': ttt.weekend,
    #                 'holiday': ttt.holiday,
    #                 'leave': ttt.leave,
    #                 'regular_days': ttt.regular_days
    #             }
    #             return super(HRChinaPayrollCreateTemp, self).create(trans_data)

    @api.multi
    def close_dialog(self):
        for item in self:
            for timesheet in item.my_id:
                trans_data = {
                    'timesheet_id': timesheet.timesheet_id.id,
                    'employee_id': timesheet.employee_id.id,
                    'start_date': timesheet.period_from,
                    'end_date': timesheet.period_to,
                    'wage_type': timesheet.wage_type,
                    'worked_days': timesheet.working_days,
                    'work_hours': timesheet.work_hours,
                    'overtime_hours': timesheet.overtime_hours,
                    'weekend': timesheet.weekend,
                    'holiday': timesheet.holiday,
                    'leave': timesheet.leave,
                    'regular_days': timesheet.regular_days
                }
                payrolls = self.env['hr_china.payslip'].create(trans_data)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }