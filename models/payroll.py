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
            item.wage_type = item.employee_id.converted_wage_type if item.employee_id else ''

    employee_id = fields.Many2one('hr.employee', string='Employee')
    name = fields.Char(string='Name', compute=_get_timesheet_name)
    wage_type = fields.Selection([('monthly', 'Monthly'), ('hourly', 'Hourly')], string='Type')
    timesheet_id = fields.Many2one('hr_china.timesheet', string='Timesheet')
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    total_days = fields.Float(string='Total Days')
    holiday_work_hours = fields.Float(string='Holiday Hours Worked', compute='_get_holiday_work_hours')
    total_work_hours = fields.Float(string='Hours Worked')
    actual_work_hours = fields.Float(string='Actual Work Hours', compute='_get_actual_wh')
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
    weekend = fields.Float(string='Weekend Working Hours') #Copied from timesheet
    holiday = fields.Float(string='Holiday Working Hours') #Copied from timesheet
    leave = fields.Float(string='Leaves') #Copied from Timsheet
    basic_pay = fields.Float(string='Basic Pay', compute='_get_basic_pay')
    total_hourly_pay = fields.Float(string='Total Hourly Pay', compute='_get_hourly_pay')
    overtime_pay = fields.Float(string='Overtime Pay', compute='_get_overtime_pay')
    holiday_pay = fields.Float(string='Holiday Pay', compute='_get_holiday_pay')
    weekend_pay = fields.Float(string='Weekend Pay', compute='_get_weekend_pay')
    regular_days = fields.Integer(string='Regular Days')

    worked_days = fields.Float(string='Weekdays Worked Days')
    weekday_ot = fields.Float(string='Weekday Overtime Pay')
    weekend_ot = fields.Float(string='Weekend Overtime Pay')
    weekend_wh = fields.Float(string='Weekend Working Hours')
    weekday_work_hours = fields.Float(string='Weekdays Work Hours', compute='_get_weekday_work_hour')
    weekend_work_hours = fields.Float(string='Weekends Working Hours', compute='_get_weekend_work_hour')
    weekend_worked_days = fields.Float(string='Weekends Worked Days', compute='_get_weekend_work_days')
    weekday_worked_days = fields.Float(string='Weekdays Worked Days', compute='_get_weekday_work_days')
    weekday_ot_hours = fields.Float(string='Weekdays Overtime Hours', compute='_get_weekday_ot')
    weekend_ot_hours = fields.Float(string='Weekends Overtime Hours', compute='_get_weekend_ot')

    weekday_hourly_pay = fields.Float(string='Weekday Hourly Pay', compute='_get_weekday_hourly_pay')
    weekday_overtime_pay = fields.Float(string='Weekday Overtime Pay', compute='_get_weekday_overtime_pay')
    weekend_hourly_pay = fields.Float(string='Weekends Hourly Pay', compute='_get_weekend_hourly_pay')
    weekend_overtime_pay = fields.Float(string='Weekends Overtime Pay', compute='_get_weekend_overtime_pay')
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_get_emp_currency')
    gross_pay = fields.Float(string='Gross Pay', compute='_get_gross_pay')

    net_pay = fields.Float(string='Net Pay', compute='_get_net_pay')

    total_benefits = fields.Float(string='Total Benefits', store=True, compute='sum_benefits')
    total_deductions = fields.Float(string='Total Deduction', compute='get_sum_deductions')

    payslip_benefits = fields.One2many('hr_china.payslip.benefits', 'payslip_id', string='Benefits')
    payslip_deductions = fields.One2many('hr_china.payslip.deductions', 'payslip_id', string='Deductions')

    @api.multi
    def _get_active_emp_contract(self):
        for item in self:
            # active_contract = self.env['hr_china.employee_contract'].search([('employee_id', '=', item.employee_id.id),
            #                                                                  ('is_active', '=', True)], limit=1)

            active_contract = self.env['hr_china.employee_contract'].search([('employee_id', '=', item.employee_id.id),
                                                                             ('start_date', '<=', item.start_date),
                                                                             ('end_date', '>=', item.end_date)])
            if active_contract:
                item.active_contract = active_contract.id

    active_contract = fields.Many2one('hr_china.employee_contract', compute=_get_active_emp_contract)

    @api.onchange('payslip_benefits')
    def sum_benefits(self):
        for benefits in self:
            total_benefits = False
            for line in benefits.payslip_benefits:
                total_benefits = total_benefits + line.amount
            benefits.total_benefits = total_benefits

    @api.onchange('payslip_deductions')
    def get_sum_deductions(self):
        for item in self:
            total_ded = False
            for line in item.payslip_deductions:
                total_ded = total_ded + line.amount
            item.total_deductions = total_ded

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
            item.currency_id = item.active_contract.currency_id.id

    @api.multi
    def _get_holiday_work_hours(self):
        for item in self:
            timesheet_trans = self.env['hr_china.timesheet.trans'].search([('timesheet', '=', item.timesheet_id.id)])
            hol_wh = 0
            for trans in timesheet_trans:
                hol_wh = hol_wh + trans.holiday_work_hours
            item.holiday_work_hours = hol_wh

    @api.multi
    def _get_weekday_work_days(self):
        for item in self:
            timesheet_trans = self.env['hr_china.timesheet.trans'].search([('timesheet', '=', item.timesheet_id.id)])
            wt = self.env['hr_china.employee_working_time'].search([('employee_id', '=', self.employee_id.id)])
            weekday_counter = 0
            for trans in timesheet_trans:
                for wtime in wt:
                    if trans.day == wtime.dayofweek:
                        if wtime.day_type == 'weekday':
                            weekday_counter = weekday_counter + 1

            item.weekday_worked_days = weekday_counter

    @api.multi
    def _get_weekend_work_days(self):
        for item in self:
            timesheet_trans = self.env['hr_china.timesheet.trans'].search([('timesheet', '=', item.timesheet_id.id)])
            wt = self.env['hr_china.employee_working_time'].search([('employee_id', '=', self.employee_id.id)])
            weekend_counter = 0
            for trans in timesheet_trans:
                for wtime in wt:
                    if trans.day == wtime.dayofweek:
                        if wtime.day_type == 'weekend':
                            weekend_counter = weekend_counter + 1

            item.weekend_worked_days = weekend_counter

    @api.multi
    def _get_weekday_work_hour(self):
        for item in self:
            timesheet_trans = self.env['hr_china.timesheet.trans'].search([('timesheet', '=', item.timesheet_id.id)])
            weekday_wh = 0
            for trans in timesheet_trans:
                weekday_wh = weekday_wh + trans.work_hours

            item.weekday_work_hours = weekday_wh

    @api.multi
    def _get_weekend_work_hour(self):
        for item in self:
            timesheet_trans = self.env['hr_china.timesheet.trans'].search([('timesheet', '=', item.timesheet_id.id)])
            weekend_wh = 0
            for trans in timesheet_trans:
                weekend_wh = weekend_wh + trans.weekend_wh

            item.weekend_work_hours = weekend_wh

    @api.multi
    def _get_weekday_ot(self):
        for item in self:
            timesheet_trans = self.env['hr_china.timesheet.trans'].search([('timesheet', '=', item.timesheet_id.id)])
            weekday_ot = 0
            for trans in timesheet_trans:
                weekday_ot = weekday_ot + trans.weekday_ot

            item.weekday_ot_hours = weekday_ot

    @api.multi
    def _get_weekend_ot(self):
        for item in self:
            timesheet_trans = self.env['hr_china.timesheet.trans'].search([('timesheet', '=', item.timesheet_id.id)])
            weekend_ot = 0
            for trans in timesheet_trans:
                weekend_ot = weekend_ot + trans.weekend_ot

            item.weekend_ot_hours = weekend_ot

    @api.multi
    def _get_actual_wh(self):
        for item in self:
            item.actual_work_hours = item.total_work_hours

    @api.onchange('employee_id')
    def _get_overtime_pay(self):
        for item in self:
            if item.start_date >= item.active_contract.start_date and item.end_date <= item.active_contract.end_date:
                ot_pay = item.overtime_hours * item.active_contract.weekday_overtime_fee
                item.overtime_pay = ot_pay

    @api.onchange('employee_id')
    def _get_weekday_hourly_pay(self):
        for item in self:
            if item.start_date >= item.active_contract.start_date and item.end_date <= item.active_contract.end_date:
                weekday_hourly_pay = item.weekday_work_hours * item.active_contract.hourly_rate
                item.weekday_hourly_pay = weekday_hourly_pay

    @api.onchange('employee_id')
    def _get_weekend_hourly_pay(self):
        for item in self:
            if item.start_date >= item.active_contract.start_date and item.end_date <= item.active_contract.end_date:
                weekend_hourly_pay = item.weekend_work_hours * item.active_contract.weekends_fee
                item.weekend_hourly_pay = weekend_hourly_pay

    @api.onchange('employee_id')
    def _get_weekday_overtime_pay(self):
        for item in self:
            if item.start_date >= item.active_contract.start_date and item.end_date <= item.active_contract.end_date:
                weekday_overtime_pay = item.weekday_ot_hours * item.active_contract.weekday_overtime_fee
                item.weekday_overtime_pay = weekday_overtime_pay

    @api.onchange('employee_id')
    def _get_weekend_overtime_pay(self):
        for item in self:
            if item.start_date >= item.active_contract.start_date and item.end_date <= item.active_contract.end_date:
                weekend_overtime_pay = item.weekend_ot_hours * item.active_contract.weekends_fee
                item.weekend_overtime_pay = weekend_overtime_pay

    @api.onchange('employee_id')
    def _get_hourly_pay(self):
        for item in self:
            if item.start_date >= item.active_contract.start_date and item.end_date <= item.active_contract.end_date:
                regular_wh_rate = item.active_contract.hourly_rate * item.actual_work_hours
                item.total_hourly_pay = regular_wh_rate

    @api.onchange('employee_id')
    def _get_basic_pay(self):
        for item in self:
            if item.start_date >= item.active_contract.start_date and item.end_date <= item.active_contract.end_date:
                mf = item.active_contract.monthly_fee
                wd = item.worked_days if item.worked_days else 1
                dim = item.regular_days if item.regular_days else 1
                item.basic_pay = (mf / dim) * wd

    @api.onchange('employee_id')
    def _get_holiday_pay(self):
        for item in self:
            times = self.env['hr_china.timesheet.trans'].search([('timesheet', '=', item.timesheet_id.id), '|',
                                                                 ('check_in_am', '!=', False),
                                                                 ('check_in_pm', '!=', False)])
            hol_list = self.env['hr_china.holiday'].search([('start_date', '>=', item.start_date),
                                                            ('end_date', '<=', item.end_date)])
            # emp = self.env['hr.employee'].search([('id', '=', item.employee_id.id)])
            # emp_hol_rate = item.active_contract.holiday_fee
            hol_rate = False
            if item.start_date >= item.active_contract.start_date and item.end_date <= item.active_contract.end_date:
                hol_rate = item.active_contract.holiday_fee

            for att in times:
                for ls in hol_list:
                    if att.date >= ls.start_date and att.date <= ls.end_date:
                        if item.active_contract.converted_wage_type == 'hourly':
                            item.holiday_pay = hol_rate * att.holiday_work_hours

    @api.onchange('employee_id')
    def _get_weekend_pay(self):
        for item in self:
            wk_pay = item.active_contract.weekends_fee if item.active_contract.weekends_fee else 0
            item.weekend_pay = wk_pay * item.weekend_wh

    @api.onchange('employee_id', 'total_benefits')
    def _get_gross_pay(self):
        for item in self:
            benefits = item.payslip_benefits
            total = False
            for line in benefits:
                total = total + line.amount
            if item.wage_type == 'monthly':
                item.gross_pay = total + item.basic_pay + item.holiday_pay + item.weekend_pay
            else:
                item.gross_pay = total + item.total_hourly_pay + item.holiday_pay + item.weekend_pay + item.overtime_pay

    @api.onchange('gross_pay', 'total_deductions')
    def _get_net_pay(self):
        for item in self:
            item.net_pay = item.gross_pay - item.total_deductions

    def print_payslip_form(self):
        payslip_id = str(self.id)
        payslip_name = self.employee_id.first_name

        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/hr_china.payslip_form/%s?filename=%s' % (payslip_id, payslip_name),
            'target': 'new'
        }

    @api.multi
    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    @api.multi
    def action_approve(self):
        for rec in self:
            rec.state = 'validate'

    @api.multi
    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.multi
    def action_update_payroll(self):
        self.ensure_one()
        if self.state == 'draft':
            times = self.env['hr_china.timesheet.trans'].search([('timesheet', '=', self.timesheet_id.id), '|',
                                                                 ('check_in_am', '!=', False),
                                                                 ('check_in_pm', '!=', False)])
            wt = self.env['hr_china.employee_working_time'].search([('employee_id', '=', self.employee_id.id)])
            ot_hours = False
            hol_ot_hours = False
            weekday_ot = False
            weekend_wh = False
            weekend_count = False
            total_wh = False
            holiday_wh = False
            for rec in times:
                ot_hours = ot_hours + rec.overtime_hours
                for wtime in wt:
                    if rec.day == wtime.dayofweek:
                        if wtime.day_type == 'weekend':
                            weekend_count = weekend_count + 1
                            weekend_wh = weekend_wh + rec.work_hours
                        else:
                            total_wh = total_wh + rec.work_hours
                            weekday_ot = weekday_ot + rec.weekday_ot

                holiday_wh = holiday_wh + rec.holiday_work_hours

            self.worked_days = len(times)
            self.overtime_hours = ot_hours
            self.actual_work_hours = total_wh - ot_hours
            self.total_work_hours = total_wh
            self.weekday_ot = weekday_ot
            self.weekend = weekend_count
            self.weekend_wh = weekend_wh
            if self.wage_type == 'hourly':
                self.holiday = holiday_wh


class HRChinaPayslipBenefits(models.Model):
    _name = 'hr_china.payslip.benefits'

    @api.onchange('benefits_id')
    def onchange_benefits_id(self):
        if self.benefits_id:
            self.benefits_id = self.benefits_id.id
            self.amount = self.benefits_id.amount
            self.currency = self.benefits_id.currency

    payslip_id = fields.Many2one('hr_china.payslip', string='Payslip')
    benefits_id = fields.Many2one('hr_china.benefits', string='Benefits')
    amount = fields.Float(string='Amount')
    currency = fields.Many2one('res.currency', string='Currency')


class HRChinaPayslipDeductions(models.Model):
    _name = 'hr_china.payslip.deductions'

    @api.onchange('deductions_id')
    def onchange_deductions_id(self):
        if self.deductions_id:
            self.deductions_id = self.deductions_id.id
            self.amount = self.deductions_id.amount
            self.currency = self.deductions_id.currency

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
        time_list = self.env['hr_china.timesheet'].search(['|', '&', ('period_from', '>=', self.start_date),
                                                                     ('period_from', '<=', self.start_date), '&',
                                                                     ('period_to', '>=', self.end_date),
                                                                     ('period_to', '<=', self.end_date)])

        for item in time_list:
            trans_data = {
                'timesheet_id': item.id,
                'employee_id': item.employee_id.id,
                'period_from': item.period_from,
                'period_to': item.period_to,
                'work_hours': item.work_time,
                'overtime_hours': item.overtime_hours,
                'weekday_ot': item.weekday_ot_hours,
                'weekend_ot': item.weekend_ot_hours,
                'weekend': item.weekend,
                'holiday': item.holiday,
                'leave': item.leaves,
                'working_days': item.total_days,
                'wage_type': item.contract_type.id,
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
    weekday_ot = fields.Float(string='Weekday Overtime')
    weekend_ot = fields.Float(string='Weekend Overtime')
    weekend = fields.Float(string='Weekends')
    holiday = fields.Float(string='Holidays')
    leave = fields.Float(string='Leaves')
    working_days = fields.Float(string='Working Days') #TOTAL DAYS EQUIVALENT
    work_hours = fields.Float(string='Work Hours') #WORK TIME EQUIVALENT
    # wage_type = fields.Selection([('monthly', 'Monthly'), ('hourly', 'Hourly')], string='Type')
    wage_type = fields.Many2one('hr_china.wage_type', string='Type')
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
    total_work_hours = fields.Float(string='Work Hours')
    overtime_hours = fields.Float(string='Overtime Hours')
    weekday_ot = fields.Float(string='Weekday Overtime')
    weekend_ot = fields.Float(string='Weekend Overtime')
    weekend = fields.Float(string='Weekends')
    holiday = fields.Float(string='Holidays')
    leave = fields.Float(string='Leaves')
    working_days = fields.Float(string='Working Days')
    regular_days = fields.Integer(string='Regular Days')
    # wage_type = fields.Selection([('monthly', 'Monthly'), ('hourly', 'Hourly')],
    #                              string='Type')
    wage_type = fields.Many2one('hr_china.wage_type', string='Type')

    @api.multi
    def close_dialog(self):
        for item in self:
            for timesheet in item.my_id:
                trans_data = {
                    'timesheet_id': timesheet.timesheet_id.id,
                    'employee_id': timesheet.employee_id.id,
                    'start_date': timesheet.period_from,
                    'end_date': timesheet.period_to,
                    'wage_type': timesheet.wage_type.wage_type,
                    'worked_days': timesheet.working_days,
                    'total_work_hours': timesheet.work_hours - timesheet.overtime_hours - timesheet.holiday,
                    'overtime_hours': timesheet.overtime_hours,
                    'weekday_ot': timesheet.weekday_ot,
                    'weekend_ot': timesheet.weekend_ot,
                    'weekend': timesheet.weekend,
                    'holiday': timesheet.holiday,
                    'leave': timesheet.leave,
                    'regular_days': timesheet.regular_days,
                }
                payrolls = self.env['hr_china.payslip'].create(trans_data)
                benefits_lines = []
                if timesheet.employee_id.employee_benefit:
                    for benefit_line in timesheet.employee_id.employee_benefit:
                        vals = {
                            'payslip_id': payrolls.id,
                            'benefits_id': benefit_line.benefits_id.id,
                            'amount': benefit_line.amount,
                            'currency': benefit_line.currency.id
                        }
                        benefits_lines.append((0, 0, vals))
                deductions_lines = []
                if timesheet.employee_id.employee_deduction:
                    for deduction_line in timesheet.employee_id.employee_deduction:
                        vals = {
                            'payslip_id': payrolls.id,
                            'deductions_id': deduction_line.deductions_id.id,
                            'amount': deduction_line.amount,
                            'currency': deduction_line.currency.id
                        }
                        deductions_lines.append((0, 0, vals))
                payrolls.payslip_benefits = benefits_lines
                payrolls.payslip_deductions = deductions_lines

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class HRChinaPayrollSummary(models.Model):
    _name = 'hr_china.payslip_summary'

    @api.model
    def get_payslip_summary(self):
        self.env['hr_china.payslip_summary'].search([]).unlink()
        emp_list = self.env['hr.employee'].search([])
        for emp in emp_list:



            trans_data = {
                'employee_id': emp.id,
                # 'wage_type': emp.c_wage_type.wage_type,
                # 'basic_pay': total_working_days,
                # 'emp_benefits': total_working_hours,
                # 'emp_deductions': payslip_gross_total,
                # 'net_pay': payslip_net_total,
                # 'gross_pay':
            }
            self.env['hr_china.payslip_summary'].create(trans_data)

            # pay_list = self.env['hr_china.payslip'].search([('employee_id', '=', emp.id)])
            # payslip_net_total = False
            # payslip_gross_total = False
            # total_working_days = False
            # total_working_hours = False
            # for payslip in pay_list:
            #     payslip_net_total = payslip_net_total + payslip.net_pay
            #     payslip_gross_total = payslip_gross_total + payslip.gross_pay
            #     total_working_days = total_working_days + payslip.total_days
            #     total_working_hours = total_working_hours + payslip.total_work_hours
            #
            # trans_data = {
            #     'employee_id': emp.id,
            #     'wage_type': emp.c_wage_type.wage_type,
            #     'total_working_days': total_working_days,
            #     'total_working_hours': total_working_hours,
            #     'payslip_gross_total': payslip_gross_total,
            #     'payslip_net_total': payslip_net_total,
            # }
            # self.env['hr_china.payslip_summary'].create(trans_data)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def _generate_name(self):
        for item in self:
            item.name = item.employee_id.name + ' - Total Payslip Summary'

    name = fields.Char(string='Name', compute=_generate_name)
    employee_id = fields.Many2one('hr.employee', 'Employee')
    wage_type = fields.Selection([('monthly', 'Monthly'), ('hourly', 'Hourly')], string='Type')
    total_working_days = fields.Float('Total Working Days')
    total_working_hours = fields.Float('Total Working Hours')
    emp_deductions = fields.Float('Monthly Benefits')
    emp_benefits = fields.Float('Monthly Deductions')
    basic_pay = fields.Float('Basic Pay')
    gross_pay = fields.Float('Gross Pay')
    net_pay = fields.Float('Net Pay')

    payslip_gross_total = fields.Float('Payslip Gross Total')
    payslip_net_total = fields.Float('Payslip Net Total')
