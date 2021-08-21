#-*- coding: utf-8 -*-

import math
from odoo import models, fields, api, _
from datetime import datetime
import time

class SpecialWorkingDays(models.Model):
    _name = 'hr_china.special_working_days'

    @api.multi
    def _compute_total_days(self):
        for item in self:
            tot_time = 0
            if item.start_date and item.end_date:
                from_dt = fields.Datetime.from_string(item.start_date)
                to_dt = fields.Datetime.from_string(item.end_date)

                time_delta = to_dt - from_dt
                tot_time = math.ceil(time_delta.days + float(time_delta.seconds) / 86400)
            item.total_days = tot_time - 1

    name = fields.Char(string='Name')
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    total_days = fields.Integer('Total Days', compute=_compute_total_days)


class HRChinaHoliday(models.Model):
    _name = 'hr_china.holiday'
    _description = 'Employee Management (Holiday)'
    _order = 'start_date asc'

    name = fields.Char('Holiday')
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')

    @api.multi
    def _compute_total_days(self):
        for item in self:
            tot_time = 0
            if item.start_date and item.end_date:
                from_dt = fields.Datetime.from_string(item.start_date)
                to_dt = fields.Datetime.from_string(item.end_date)

                time_delta = to_dt - from_dt
                tot_time = math.ceil(time_delta.days + float(time_delta.seconds) / 86400)
            item.total_days = tot_time - 1

    total_days = fields.Integer('Total Days', compute=_compute_total_days)


class HRChinaContractTemplateWorkingTime(models.Model):
    _name = 'hr_china.template_working_time'
    _description = 'List of Employee Working Time'
    _order = 'sequence'

    name = fields.Char(string='Name')
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, default='0')
    date_from = fields.Date(string='Starting Date')
    date_to = fields.Date(string='End Date')
    hour_from = fields.Float(string='Work from', required=True, index=True, help="Start and End time of working.")
    hour_to = fields.Float(string='Work to', required=True)
    sequence = fields.Integer('Sequence')


class HRBenefits(models.Model):
    _name = 'hr_china.benefits'

    @api.multi
    def _get_currency_default(self):
        cny = self.env['res.currency'].search([('name', '=', 'CNY')])
        if cny: return cny.id

    name = fields.Char('Name')
    benefit_type = fields.Selection([('one-time', 'One Time'), ('monthly', 'Monthly'), ('yearly', 'Yearly')], string='Type')
    amount = fields.Float('Amount')
    currency = fields.Many2one('res.currency', string="Currency", default=_get_currency_default)


class HRDeductions(models.Model):
    _name = 'hr_china.deductions'

    @api.multi
    def _get_currency_default(self):
        cny = self.env['res.currency'].search([('name', '=', 'CNY')])
        if cny: return cny.id

    name = fields.Char('Name')
    deduction_type = fields.Selection([('one-time', 'One Time'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
                                    string='Type')
    amount = fields.Float('Amount')
    currency = fields.Many2one('res.currency', string="Currency", default=_get_currency_default)


class HRContractTemplate(models.Model):
    _name = 'hr_china.contracts_template'

    name = fields.Char('Name')
    wage_type = fields.Selection([('hourly', 'Hourly'), ('monthly', 'Monthly')], default="hourly",
                                 string='Wage Type', required=True)
    monthly_fee = fields.Float(string='Monthly Fee')
    weekday_daily_fee = fields.Float(string='Weekly Daily Fee')
    weekday_overtime_fee = fields.Float(string='Weekday Overtime Fee')
    weekends_fee = fields.Float(string='Weekends Fee')
    holiday_fee = fields.Float(string='Holiday Fee')
    dayoff_deduction = fields.Float(string='Day Off Deduction')
    other_info = fields.Text(string='Additional Information')

    working_time = fields.Many2many('hr_china.template_working_time', string='Working Time')
    benefits_id = fields.Many2many('hr_china.benefits', string='Benefits')
    deductions_id = fields.Many2many('hr_china.deductions', string='Deductions')


class HRJobTitles(models.Model):
    _name = 'hr_china.job_titles'

    name = fields.Char('Name')
    department = fields.Many2one('hr.department', string='Department')
    is_active = fields.Boolean('Active', default=True)


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    first_name = fields.Char('First Name')
    second_name = fields.Char('Second Name')
    middle_name = fields.Char('Middle Name')
    nick_name = fields.Char('Nick Name')

    contact_number = fields.Char('Contact Number')
    emergency_contact_number = fields.Char('Emergency Contact No')
    emergency_contact_name = fields.Char('Emergency Contact Name')
    emergency_contact_relation = fields.Char('Emergency Contact Relation')
    citizenship = fields.Char('Citizenship')
    bank_name = fields.Char('Beneficiary Bank')
    bank_branch = fields.Char('Beneficiary Bank Branch')
    account_name = fields.Char('Beneficiary Account Name')
    account_number = fields.Char('Beneficiary Account Number')
    identification_image = fields.Binary('Identification Image')

    contract_template_id = fields.Many2one('hr_china.contracts_template', string='Contract Template ID')
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')

    contract_name = fields.Char()
    c_wage_type = fields.Selection([('hourly', 'Hourly'), ('monthly', 'Monthly')], default="hourly",
                                 string='Wage Type')
    c_monthly_fee = fields.Float(string='Monthly Fee')
    c_weekday_daily_fee = fields.Float(string='Weekly Daily Fee')
    c_weekday_overtime_fee = fields.Float(string='Weekday Overtime Fee')
    c_weekends_fee = fields.Float(string='Weekends Fee')
    c_holiday_fee = fields.Float(string='Holiday Fee')
    c_dayoff_deduction = fields.Float(string='Day Off Deduction')
    c_other_info = fields.Text(string='Additional Information')
    c_is_contract_active = fields.Boolean()

    @api.multi
    def _get_active_contract(self):
        for item in self:
            emp_contracts = self.env['hr_china.contract'].search(
                [('employee_id', '=', item.id)], order='start_date DESC')
            active_contract = False
            for empc in emp_contracts:
                if empc.is_contract_active:
                    active_contract = empc.id
                    break
            if active_contract:
                item.active_contract = active_contract

    employee_benefit = fields.One2many('hr_china.employee_benefits', 'employee_id', string='Benefits')
    employee_deduction = fields.One2many('hr_china.employee_deductions', 'employee_id', string='Deductions')
    employee_working_time = fields.One2many('hr_china.employee_working_time', 'employee_id', string='Working Time')
    new_contract_id = fields.One2many('hr_china.contract', 'employee_id', string='Contract')
    all_contracts = fields.Many2many('hr_china.contract', string='All Contracts')
    active_contract = fields.Many2one('hr_china.contract', string='Active Contract', compute=_get_active_contract)
    is_contract_active = fields.Boolean('Contract is Active')

    @api.onchange('contract_template_id')
    def contract_templ_change(self):
        templ_contract = self.contract_template_id
        working_time_lines = []
        for working_line in self.contract_template_id.working_time:
            vals = {
                'employee_id': self.id,
                'name': working_line.name,
                'dayofweek': working_line.dayofweek,
                'date_from': working_line.date_from,
                'date_to': working_line.date_to,
                'hour_from': working_line.hour_from,
                'hour_to': working_line.hour_to,
            }
            working_time_lines.append((0, 0, vals))

        benefits_lines = []
        for benefit_line in self.contract_template_id.benefits_id:
            vals = {
                'employee_id': self.id,
                'benefits_id': benefit_line.id,
                'benefit_type': benefit_line.benefit_type,
                'amount': benefit_line.amount,
            }
            benefits_lines.append((0, 0, vals))

        deductions_lines = []
        for deduction_line in self.contract_template_id.deductions_id:
            vals = {
                'employee_id': self.id,
                'deductions_id': deduction_line.id,
                'deduction_type': deduction_line.deduction_type,
                'amount': deduction_line.amount,
            }
            deductions_lines.append((0, 0, vals))

        self.employee_benefit = benefits_lines
        self.employee_deduction = deductions_lines
        self.employee_working_time = working_time_lines

        if templ_contract:
            self.contract_name = self.name + " - " + templ_contract.name
            self.c_wage_type = templ_contract.wage_type
            self.c_monthly_fee = templ_contract.monthly_fee
            self.c_weekday_daily_fee = templ_contract.weekday_daily_fee
            self.c_weekday_overtime_fee = templ_contract.weekday_overtime_fee
            self.c_weekends_fee = templ_contract.weekends_fee
            self.c_holiday_fee = templ_contract.holiday_fee
            self.c_dayoff_deduction = templ_contract.dayoff_deduction
            self.c_other_info = templ_contract.other_info
            self.c_working_time = templ_contract.working_time
            self.c_benefits_id = templ_contract.benefits_id
            self.c_deductions_id = templ_contract.deductions_id
        else:
            self.contract_name = False
            self.start_date = False
            self.end_date = False
            self.c_wage_type = False
            self.c_monthly_fee = False
            self.c_weekday_daily_fee = False
            self.c_weekday_overtime_fee = False
            self.c_weekends_fee = False
            self.c_holiday_fee = False
            self.c_dayoff_deduction = False
            self.c_other_info = False
            self.c_working_time = False
            self.c_benefits_id = False
            self.c_deductions_id = False

    @api.multi
    def write(self, vals):
        ret_val = super(HREmployee, self).write(vals)

        if 'all_contracts' not in vals and 'new_contract_id' not in vals:
            if 'contract_template_id' in vals:

                if vals['contract_template_id']:
                    created_contract = self.env['hr_china.contract'].create({
                        'employee_id': self.id,
                        'name': self.contract_name,
                        'wage_type': self.contract_template_id.wage_type,
                        'monthly_fee': self.contract_template_id.monthly_fee,
                        'weekday_daily_fee': self.contract_template_id.weekday_daily_fee,
                        'weekday_overtime_fee': self.contract_template_id.weekday_overtime_fee,
                        'weekends_fee': self.contract_template_id.weekends_fee,
                        'holiday_fee': self.contract_template_id.holiday_fee,
                        'dayoff_deduction': self.contract_template_id.dayoff_deduction,
                        'other_info': self.contract_template_id.other_info,
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'contract_template_id': self.contract_template_id.id
                    })

                    self.new_contract_id = created_contract
                    self.all_contracts = [[4, created_contract.id]]

                    working_time_lines = []
                    for working_line in self.contract_template_id.working_time:
                        vals = {
                            'contract_id': created_contract.id,
                            'name': working_line.name,
                            'dayofweek': working_line.dayofweek,
                            'date_from': working_line.date_from,
                            'date_to': working_line.date_to,
                            'hour_from': working_line.hour_from,
                            'hour_to': working_line.hour_to,
                        }
                        working_time_lines.append((0, 0, vals))

                    benefits_lines = []
                    for benefit_line in self.contract_template_id.benefits_id:
                        vals = {
                            'contract_id': created_contract.id,
                            'benefits_id': benefit_line.id,
                            'benefit_type': benefit_line.benefit_type,
                            'amount': benefit_line.amount,
                        }
                        benefits_lines.append((0, 0, vals))

                    deductions_lines = []
                    for deduction_line in self.contract_template_id.deductions_id:
                        vals = {
                            'contract_id': created_contract.id,
                            'deductions_id': deduction_line.id,
                            'deduction_type': deduction_line.deduction_type,
                            'amount': deduction_line.amount,
                        }
                        deductions_lines.append((0, 0, vals))

                    created_contract.benefits_id = benefits_lines
                    created_contract.deductions_id = deductions_lines
                    created_contract.working_time = working_time_lines

        active_cont_dict = {}
        if 'c_holiday_fee' in vals:
            active_cont_dict['holiday_fee'] = vals['c_holiday_fee']
        if 'c_dayoff_deduction' in vals:
            active_cont_dict['dayoff_deduction'] = vals['c_dayoff_deduction']
        if 'c_wage_type' in vals:
            active_cont_dict['wage_type'] = vals['c_wage_type']
        if 'c_monthly_fee' in vals:
            active_cont_dict['monthly_fee'] = vals['c_monthly_fee']
        if 'c_weekday_daily_fee' in vals:
            active_cont_dict['weekday_daily_fee'] = vals['c_weekday_daily_fee']
        if 'c_weekday_overtime_fee' in vals:
            active_cont_dict['weekday_overtime_fee'] = vals['c_weekday_overtime_fee']
        if 'c_weekends_fee' in vals:
            active_cont_dict['weekends_fee'] = vals['c_weekends_fee']
        if 'start_date' in vals:
            active_cont_dict['start_date'] = vals['start_date']
        if 'end_date' in  vals:
            active_cont_dict['end_date'] = vals['end_date']
        if 'is_contract_active' in vals:
            active_cont_dict['is_contract_active'] = vals['is_contract_active']

        if len(active_cont_dict) > 0:
            #self.active_contract.write(active_cont_dict)
            self.new_contract_id.write(active_cont_dict)
            # self.all_contracts.write(active_cont_dict)

        return ret_val


class HRChinaContract(models.Model):
    _name = 'hr_china.contract'
    _order = 'id'

    @api.multi
    def _check_contract_status(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if datetime.strptime(rec.start_date, "%Y-%m-%d %H:%M:%S") <= datetime.now() <= \
                        datetime.strptime(rec.end_date, "%Y-%m-%d %H:%M:%S"):
                    rec.is_contract_active = 'active'
                    rec.active = True
                else:
                    rec.is_contract_active = 'expired'
                    rec.active = False

    employee_id = fields.Many2one('hr.employee', string='Employee')
    active = fields.Boolean(string='Active', default=True)
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    contract_template_id = fields.Many2one('hr_china.contracts_template')
    #is_contract_active = fields.Boolean('Contract is Active', compute=_check_contract_status)
    is_contract_active = fields.Selection([('expired', 'Expired'), ('active', 'Active')])
    name = fields.Char('Name')
    wage_type = fields.Selection([('hourly', 'Hourly'), ('monthly', 'Monthly')], default="hourly",
                                 string='Wage Type')
    monthly_fee = fields.Float(string='Monthly Fee')
    weekday_daily_fee = fields.Float(string='Weekly Daily Fee')
    weekday_overtime_fee = fields.Float(string='Weekday Overtime Fee')
    weekends_fee = fields.Float(string='Weekends Fee')
    holiday_fee = fields.Float(string='Holiday Fee')
    dayoff_deduction = fields.Float(string='Day Off Deduction')
    other_info = fields.Text(string='Additional Information')

    working_time = fields.One2many('hr_china.contract_working_time', 'contract_id',
                                   string='Working Time')
    benefits_id = fields.One2many('hr_china.contract_benefits', 'contract_id',
                                  string='Benefits')
    deductions_id = fields.One2many('hr_china.contract_deductions', 'contract_id',
                                    string='Deductions')


class HRChinaContractBenefits(models.Model):
    _name = 'hr_china.contract_benefits'

    @api.multi
    def _get_currency_default(self):
        cny = self.env['res.currency'].search([('name', '=', 'CNY')])
        if cny:
            return cny.id

    contract_id = fields.Many2one('hr_china.contract', string='Contract')
    benefit_type = fields.Selection([('one-time', 'One Time'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
                                    string='Type')
    benefits_id = fields.Many2one('hr_china.benefits', string='Name')
    amount = fields.Float('Amount')
    currency = fields.Many2one('res.currency', string="Currency", default=_get_currency_default)


class HRChinaContractDeductions(models.Model):
    _name = 'hr_china.contract_deductions'

    @api.multi
    def _get_currency_default(self):
        cny = self.env['res.currency'].search([('name', '=', 'CNY')])
        if cny:
            return cny.id

    contract_id = fields.Many2one('hr_china.contract', string='Contract')
    deduction_type = fields.Selection([('one-time', 'One Time'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
                                      string='Type')
    deductions_id = fields.Many2one('hr_china.deductions', string='Name')
    amount = fields.Float('Amount')
    currency = fields.Many2one('res.currency', string="Currency", default=_get_currency_default)


class HRChinaContractWorkingTime(models.Model):
    _name = 'hr_china.contract_working_time'

    contract_id = fields.Many2one('hr_china.contract', string='Contract')
    name = fields.Char(string='Name')
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, default='0')
    date_from = fields.Date(string='Starting Date')
    date_to = fields.Date(string='End Date')
    hour_from = fields.Float(string='Work from', required=True, index=True, help="Start and End time of working.")
    hour_to = fields.Float(string='Work to', required=True)


class HRChinaEmployeeBenefits(models.Model):
    _name = 'hr_china.employee_benefits'
    _description = 'List of Employee Benefits'

    @api.multi
    def _get_currency_default(self):
        cny = self.env['res.currency'].search([('name', '=', 'CNY')])
        if cny:
            return cny.id

    @api.onchange('benefits_id')
    def onchange_benefits_id(self):
        if self.benefits_id:
            self.benefits_id = self.benefits_id.id
            self.benefit_type = self.benefits_id.benefit_type
            self.amount = self.benefits_id.amount
            self.currency = self.benefits_id.currency

    employee_id = fields.Many2one('hr.employee', string='Employee')
    contract_id = fields.Many2one('hr_china.contract', string='Contract')
    benefit_type = fields.Selection([('one-time', 'One Time'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
                                    string='Type')
    benefits_id = fields.Many2one('hr_china.benefits', string='Name')
    amount = fields.Float('Amount')
    currency = fields.Many2one('res.currency', string="Currency", default=_get_currency_default)


class HRChinaEmployeeDeductions(models.Model):
    _name = 'hr_china.employee_deductions'
    _description = 'List of Employee Salary Deductions'

    @api.multi
    def _get_currency_default(self):
        cny = self.env['res.currency'].search([('name', '=', 'CNY')])
        if cny:
            return cny.id

    @api.onchange('deductions_id')
    def onchange_deductions_id(self):
        if self.deductions_id:
            self.deductions_id = self.deductions_id.id
            self.deduction_type = self.deductions_id.deduction_type
            self.amount = self.deductions_id.amount
            self.currency = self.deductions_id.currency

    employee_id = fields.Many2one('hr.employee', string='Employee')
    contract_id = fields.Many2one('hr_china.contract', string='Contract')
    deduction_type = fields.Selection([('one-time', 'One Time'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
                                      string='Type')
    deductions_id = fields.Many2one('hr_china.deductions', string='Name')
    amount = fields.Float('Amount')
    currency = fields.Many2one('res.currency', string="Currency", default=_get_currency_default)


class HRChinaEmployeeWorkingTime(models.Model):
    _name = 'hr_china.employee_working_time'
    _description = 'List of Employee Working Time'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    contract_id = fields.Many2one('hr_china.contract', string='Contract')
    name = fields.Char(string='Name')
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, default='0')
    date_from = fields.Date(string='Starting Date')
    date_to = fields.Date(string='End Date')
    hour_from = fields.Float(string='Work from', required=True, index=True, help="Start and End time of working.")
    hour_to = fields.Float(string='Work to', required=True)


class HRChinaAttendance(models.Model):
    _inherit = 'hr.employee'

    def show_emp_attendance(self):
        return {
            'name': 'Attendance',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'hr.attendance',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'self',
            'context': {
                'search_default_employee_id': self.id
            }
        }