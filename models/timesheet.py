# -*- coding: utf-8 -*-

import math
from odoo import models, fields, api, exceptions, _, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta, date, time
from odoo.exceptions import UserError, AccessError, ValidationError
import calendar
import time


class HRTimesheet(models.Model):
    _name = "hr_china.timesheet"

    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department', compute='_get_department', stored=True)
    job_title_id = fields.Many2one('hr_china.job_titles', string='Position', compute='_get_job_title', stored=True)
    period_from = fields.Datetime(string='Date From')
    period_to = fields.Datetime(string='Date To')
    attendance_id = fields.Many2many('hr_china.attendance', string='Attendance')
    regular_days = fields.Integer(string='Regular Days', compute='_get_regular_days')
    overtime_hours = fields.Float(string='Overtime Hours', compute='_get_overtime_work')
    weekend = fields.Float(string='Weekends', compute='_get_weekends')
    holiday = fields.Float(string='Holidays', compute='_get_holiday_list')
    leaves = fields.Float(string='Leaves', compute='_get_leave_list')
    total_days = fields.Float(string='Total Days', compute='_get_total_days')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('validate', 'Approved')],
                             string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft')
    timesheet_state = fields.Html(string='Status', compute='_get_timesheet_state')

    name = fields.Char(string='Name', compute='_get_employee_name')
    employee_image = fields.Binary(compute='_get_employee_image')

    attendance_trans = fields.One2many('hr_china.timesheet.trans', 'timesheet')
    contract_type = fields.Many2one('hr_china.wage_type', string='Contract Type')
    # contract_type = fields.Char(string='Contract Type', compute='_get_contract_type', stored=True)
    work_time = fields.Float(string='Work Time', compute='_get_work_time')

    def print_timesheet_form(self):
        timesheet_id = str(self.id)
        timesheet_name = self.name

        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/hr_china.timesheet_form_rpt/%s?filename=%s' % (timesheet_id, timesheet_name),
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
    def _get_employee_image(self):
        for item in self:
            item.employee_image = item.employee_id.image

    @api.multi
    def _get_department(self):
        for item in self:
            item.department_id = item.employee_id.department_id

    @api.multi
    def _get_job_title(self):
        for item in self:
            item.job_title_id = item.employee_id.job_new_id

    @api.multi
    def _gen_timesheet_name(self):
        for item in self:
            item.name = item.employee_id.name + ' ' + item.period_from + ' - ' + item.period_to + ' Timesheet'

    @api.multi
    def _get_employee_name(self):
        for item in self:
            item.name = item.employee_id.name + ' - Timesheet' if item.employee_id else ''

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
            item.timesheet_state = '<span class="item_badge" style="background-color:%s;">%s</span>' % (color, ret_val)

    # @api.onchange('employee_id')
    # def _get_contract_type(self):
    #     for item in self:
    #         contract = self.env['hr.employee'].search([('id', '=', item.employee_id.id)])
    #         item.contract_type = contract.c_wage_type.id

    @api.onchange('employee_id')
    def _get_regular_days(self):
        for item in self:
            employee = self.env['hr.employee'].search([('id', '=', item.employee_id.id)])
            contract_temp = employee.contract_template_id.id
            ct = self.env['hr_china.contracts_template'].search([('id', '=', contract_temp)])
            item.regular_days = ct.wage_type.days

    @api.onchange('period_from', 'period_to')
    def _get_holiday_list(self):
        for item in self:
            holiday_list = self.env['hr_china.holiday'].search([('start_date', '>=', item.period_from),
                                                                ('start_date', '<=', item.period_from),
                                                                ('end_date', '>=', item.period_to),
                                                                ('end_date', '<=', item.period_to)])

            item.holiday = len(holiday_list) if holiday_list else 0

    @api.onchange('employee_id')
    def _get_leave_list(self):
        for item in self:
            pass

    @api.onchange('employee_id')
    def _get_overtime_work(self):
        for item in self:
            ot = self.env['hr_china.attendance'].search([('employee_id', '=', item.employee_id.id),
                                                         ('attendance_date', '>=', item.period_from),
                                                         ('attendance_date', '<=', item.period_to)])
            ot_hours = False
            for overtime in ot:
                ot_hours = ot_hours + overtime.overtime_hours
            item.overtime_hours = ot_hours

    @api.onchange('employee_id')
    def _get_work_time(self):
        for item in self:
            wh = self.env['hr_china.attendance'].search([('employee_id', '=', item.employee_id.id),
                                                         ('attendance_date', '>=', item.period_from),
                                                         ('attendance_date', '<=', item.period_to)])
            wh_hours = False
            for wtime in wh:
                wh_hours = wh_hours + wtime.work_hours
            item.work_time = wh_hours

    @api.onchange('employee_id')
    def _get_total_days(self):
        for item in self:
            td = self.env['hr_china.attendance'].search([('employee_id', '=', item.employee_id.id),
                                                         ('attendance_date', '>=', item.period_from),
                                                         ('attendance_date', '<=', item.period_to)])

            item.total_days = len(td) if td else 0

    @api.onchange('employee_id')
    def _get_weekends(self):
        for item in self:
            wks = self.env['hr_china.attendance'].search([('employee_id', '=', item.employee_id.id),
                                                         ('attendance_date', '>=', item.period_from),
                                                         ('attendance_date', '<=', item.period_to)])
            weekend_count = False
            for day in wks:
                if day.attendance_day == 5 or day.attendance_day == 6:
                    weekend_count = weekend_count + 1

            item.weekend = weekend_count

    @api.multi
    def create_attendance_trans(self):
        context = self.env.context
        for item in self:
            frmt = '%Y-%m-%d %H:%M:%S'
            st = datetime.strptime(item.period_from, frmt)
            end = datetime.strptime(item.period_to, frmt)
            st_y = int(st.strftime("%Y"))
            st_m = int(st.strftime("%m"))
            st_d = int(st.strftime("%d"))
            end_y = int(end.strftime("%Y"))
            end_m = int(end.strftime("%m"))
            end_d = int(end.strftime("%d"))

            dt1 = date(st_y, st_m, st_d)
            dt2 = date(end_y, end_m, end_d)
            delta = dt2 - dt1
            employee = item.employee_id

            for i in range(delta.days + 1):
                day = dt1 + timedelta(days=i)
                date_i = day.strftime(frmt)

                base_date = date_i.split(' ')
                base_date[1] = '23:59:59'
                base_date_2 = date_i.split(' ')
                base_date_2[1] = '00:00:00'
                base_date_0 = ' '.join(base_date_2)
                base_date_23 = ' '.join(base_date)

                #GET Holidays
                holiday_lis = self.env['hr_china.holiday'].search(
                    ['|', '&', ('start_date', '<=', base_date_0), ('end_date', '>=', base_date_23),
                     ('end_date', '=', base_date_0)], limit=1)

                same_dates = self.env['hr_china.attendance'].search(
                    [('employee_id', '=', employee.id), ('attendance_date', '>=', base_date_0),
                     ('attendance_date', '<=', base_date_23)])

                trans_data = {
                    'timesheet': item.id,
                    'date': day
                }

                if len(same_dates) > 0:
                    trans_data['day'] = same_dates[0].attendance_day
                    trans_data['check_in_am'] = same_dates[0].check_in_am if same_dates[0].check_in_am else False
                    trans_data['check_out_am'] = same_dates[0].check_out_am if same_dates[0].check_out_am else False
                    trans_data['check_in_pm'] = same_dates[0].check_in_pm if same_dates[0].check_in_pm else False
                    trans_data['check_out_pm'] = same_dates[0].check_out_pm if same_dates[0].check_out_pm else False
                    trans_data['break_hours'] = same_dates[0].break_hours if same_dates[0].break_hours else False
                    trans_data['work_hours'] = same_dates[0].work_hours if same_dates[0].work_hours else False
                    trans_data['overtime_hours'] = same_dates[0].overtime_hours if same_dates[0].overtime_hours else False
                self.env['hr_china.timesheet.trans'].create(trans_data)
        return True

    @api.model
    def create(self, vals):
        if 'derivative_create' not in self.env.context:
            if 'employee_ids' in vals:
                emps = vals['employee_ids'][0][2]
                vals['employee_id'] = emps[0]
                del emps[0]
                for emp in emps:
                    self.env['hr_china.timesheet'].with_context({
                        'derivative_create': 1
                    }).create({
                        'employee_id': emp,
                        'period_from': vals['period_from'],
                        'period_to': vals['period_to']
                    })
            elif 'employee_ids' not in vals and 'derivative_create' not in self.env.context:
                raise UserError(_('Select Users'))
        timesheet = super(HRTimesheet, self).create(vals)
        timesheet.create_attendance_trans()


class HRChinaTrans(models.Model):
    _name = 'hr_china.timesheet.trans'

    @api.onchange('check_in_pm')
    @api.depends('check_out_am', 'check_in_pm')
    def compute_break_hours(self):
        for attendance in self:
            if attendance.check_out_am and attendance.check_in_pm:
                break_hours_delta = datetime.strptime(attendance.check_in_pm, DEFAULT_SERVER_DATETIME_FORMAT) - \
                                    datetime.strptime(attendance.check_out_am, DEFAULT_SERVER_DATETIME_FORMAT)
                attendance.break_hours = break_hours_delta.total_seconds() / 3600.0

    date = fields.Datetime(string='Date')
    hr_attendance = fields.Many2one('hr_china.attendance')
    timesheet = fields.Many2one('hr_china.timesheet', ondelete='cascade')

    day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], string='Day')
    check_in_am = fields.Datetime(string='Morning Check-In')
    check_out_am = fields.Datetime(string='Morning Check-Out')
    check_in_pm = fields.Datetime(string='Afternoon Check-In')
    check_out_pm = fields.Datetime(string='Afternoon Check-Out')
    break_hours = fields.Float(string='Break Hours', compute=compute_break_hours)
    work_hours = fields.Float(string='Worked Hours', compute='_get_work_time')
    overtime_hours = fields.Float(string='Overtime Hours', compute='_get_overtime_work')
    weekend = fields.Float(string='Weekends')
    date_day = fields.Char('Day', compute='_get_day_of_date')

    @api.onchange('check_out_am', 'check_out_pm')
    def _get_overtime_work(self):
        for item in self:
            working_time = self.env['hr_china.employee_working_time'].search([
                ('employee_id', '=', item.timesheet.employee_id.id),
                ('dayofweek', '=', item.day)
            ], order='id DESC')
            reg_hours = (working_time.hour_to - working_time.hour_from) - working_time.break_hours
            ot_hours = item.work_hours - reg_hours

            if ot_hours > 0:
                item.overtime_hours = ot_hours

    @api.onchange('check_in_am', 'check_out_am', 'check_in_pm', 'check_out_pm')
    def _get_work_time(self):
        for item in self:
            morning_wh = False
            afternoon_wh = False
            if item.check_out_am and item.check_in_am:
                morning_wh_delta = datetime.strptime(item.check_out_am, DEFAULT_SERVER_DATETIME_FORMAT) - \
                                   datetime.strptime(item.check_in_am, DEFAULT_SERVER_DATETIME_FORMAT)
                morning_wh = morning_wh_delta.total_seconds() / 3600.0
            if item.check_out_pm and item.check_in_pm:
                afternoon_wh_delta = datetime.strptime(item.check_out_pm, DEFAULT_SERVER_DATETIME_FORMAT) - \
                                     datetime.strptime(item.check_in_pm, DEFAULT_SERVER_DATETIME_FORMAT)
                afternoon_wh = afternoon_wh_delta.total_seconds() / 3600.0

            if not morning_wh:
                morning_wh = 0
            if not afternoon_wh:
                afternoon_wh = 0

            total_wh = afternoon_wh + morning_wh
            item.work_hours = total_wh

    @api.onchange('date')
    def _get_day_of_date(self):
        for r in self:
            selected = fields.Datetime.from_string(r.date)
            r.date_day = calendar.day_abbr[selected.weekday() if selected else 0]

    @api.multi
    def _get_checkin_am_str(self):
        for item in self:
            if item.check_in_am:
                frmt = '%Y-%m-%d %H:%M:%S'
                st = datetime.strptime(item.check_in_am, frmt)
                end_ad = st + timedelta(hours=8, minutes=0)
                end = end_ad.strftime("%H:%M")
                x = str(end)
                item.check_in_am_str = x

    @api.multi
    def _get_checkout_am_str(self):
        for item in self:
            if item.check_out_am:
                frmt = '%Y-%m-%d %H:%M:%S'
                st = datetime.strptime(item.check_out_am, frmt)
                end_ad = st + timedelta(hours=8, minutes=0)
                end = end_ad.strftime("%H:%M")
                x = str(end)
                item.check_out_am_str = x

    @api.multi
    def _get_checkin_pm_str(self):
        for item in self:
            if item.check_in_pm:
                frmt = '%Y-%m-%d %H:%M:%S'
                st = datetime.strptime(item.check_in_pm, frmt)
                end_ad = st + timedelta(hours=8, minutes=0)
                end = end_ad.strftime("%H:%M")
                x = str(end)
                item.check_in_pm_str = x

    @api.multi
    def _get_checkout_pm_str(self):
        for item in self:
            if item.check_out_pm:
                frmt = '%Y-%m-%d %H:%M:%S'
                st = datetime.strptime(item.check_out_pm, frmt)
                end_ad = st + timedelta(hours=8, minutes=0)
                end = end_ad.strftime("%H:%M")
                x = str(end)
                item.check_out_pm_str = x

    check_in_am_str = fields.Char(compute=_get_checkin_am_str)
    check_out_am_str = fields.Char(compute=_get_checkout_am_str)
    check_in_pm_str = fields.Char(compute=_get_checkin_pm_str)
    check_out_pm_str = fields.Char(compute=_get_checkout_pm_str)


class HRChinaTimesheetCreate(models.TransientModel):
    _name = 'hr_china.timesheet.create'
    _description = 'For attendance timesheet create'

    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    employee_ids = fields.Many2many('hr.employee')

    @api.model
    def do_get_display(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr_china.timesheet.create',
            'name': 'Timesheet',
            'views': [(False, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.multi
    def close_dialog(self):
        self.env['hr_china.timesheet'].create({
            'employee_ids': [[6, 0, self.employee_ids.ids]],
            'period_from': self.start_date,
            'period_to': self.end_date,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class HREmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee Management'

    @api.model
    def attendance_scan(self, barcode):
        """ Receive a barcode scanned from the Kiosk Mode and change the attendances of corresponding employee.
            Returns either an action or a warning.
        """
        employee = self.search([('barcode', '=', barcode)], limit=1)
        config = self.env['zulu_attendance.configuration'].search([], order='id desc', limit=1)
        my_action = False
        cust_action = 'none'
        now_date = datetime.now().date()
        from_date = datetime.strftime(now_date, '%Y-%m-%d 00:00:00')
        to_date = datetime.strftime(now_date, '%Y-%m-%d 23:59:00')
        # Duplicate fix: no scan for the same person within specified secs ###
        last_attendance_obj = self.env['hr_china.attendance'].search([
            ('employee_id', '=', employee.id),
            ('attendance_date', '>=', from_date),
            ('attendance_date', '<=', to_date)
        ], order='id desc', limit=1)

        if last_attendance_obj:
            if last_attendance_obj.check_out_pm and not last_attendance_obj.check_in_am:
                last_activity_time = last_attendance_obj.check_out_pm
                my_action = 'check_in_am'
                # cust_action = 'no_action'

                if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                        last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):

                    return employee and employee.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                                                   time_action=my_action, custom_action='no_action') or \
                           {'warning': _('YOU HAVE ALREADY CHECKED OUT.') % {'employee': employee.name.split()[0]}}

            if last_attendance_obj.check_out_am and not last_attendance_obj.check_in_pm:
                last_activity_time = last_attendance_obj.check_out_am
                my_action = 'check_in_pm'
                # cust_action = 'no_action'

                if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                        last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):

                    return employee and employee.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                                                   time_action=my_action, custom_action='no_action') or \
                           {'warning': _('YOU HAVE ALREADY CHECKED OUT.') % {'employee': employee.name.split()[0]}}

            if last_attendance_obj.check_in_am and not last_attendance_obj.check_out_am:
                last_activity_time = last_attendance_obj.check_in_am
                my_action = 'check_out_am'
                # cust_action = 'no_action'

                if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                        last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):

                    return employee and employee.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                                                   time_action=my_action, custom_action='no_action') or \
                           {'warning': _('YOU HAVE ALREADY CHECKED IN.') % {'employee': employee.name.split()[0]}}

            if last_attendance_obj.check_in_pm and not last_attendance_obj.check_out_pm:
                last_activity_time = last_attendance_obj.check_in_pm
                my_action = 'check_out_pm'
                # cust_action = 'no_action'

                if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                        last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):

                    return employee and employee.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                                                   time_action=my_action, custom_action='no_action') or \
                           {'warning': _('YOU HAVE ALREADY CHECKED IN.') % {'employee': employee.name.split()[0]}}

        else:
            action_date = fields.Datetime.now()
            mid_day = datetime(2021, 01, 01, 12, 0, 0)
            hours = timedelta(hours=8)
            if (datetime.strptime(action_date, DEFAULT_SERVER_DATETIME_FORMAT) + hours).time() < mid_day.time():
                my_action = 'check_in_am'
                # return employee and employee.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                #                                                time_action=my_action) or \
                #        {'warning': _('No employee corresponding to barcode %(barcode)s') % {'barcode': barcode}}
            else:
                my_action = 'check_in_pm'
                # return employee and employee.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                #                                                time_action=my_action) or \
                #        {'warning': _('No employee corresponding to barcode %(barcode)s') % {'barcode': barcode}}
        # End of fix
        return employee and employee.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                                       time_action=my_action, custom_action=cust_action) or \
               {'warning': _('No employee corresponding to barcode %(barcode)s') % {'barcode': barcode}}

    @api.multi
    def attendance_manual(self, next_action, entered_pin=None):
        self.ensure_one()

        config = self.env['zulu_attendance.configuration'].search([], order='id desc', limit=1)
        now_date = datetime.now().date()
        from_date = datetime.strftime(now_date, '%Y-%m-%d 00:00:00')
        to_date = datetime.strptime(now_date, '%Y-%m-%d 23:59:00')
        last_attendance_obj = self.env['hr_china.attendance'].search([
            ('employee_id', '=', self.id),
            ('attendance_date', '>=', from_date),
            ('attendanace_date', '<=', to_date)
        ], order='id desc', limit=1)

        my_action = False
        cust_action = 'none'
        if last_attendance_obj:
            if last_attendance_obj.check_out_pm and not last_attendance_obj.check_in_am:
                last_activity_time = last_attendance_obj.check_out_pm
                my_action = 'check_in_am'

                if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                        last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):

                    return self and self.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                                  time_action=my_action, custom_action='no_action') or \
                           {'warning': _('YOU HAVE ALREADY CHECKED OUT.') % {'employee': self.name.split()[0]}}

            if last_attendance_obj.check_out_am and not last_attendance_obj.check_in_pm:
                last_activity_time = last_attendance_obj.check_out_am
                my_action = 'check_in_pm'

                if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                        last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):

                    return self and self.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                                  time_action=my_action, custom_action='no_action') or \
                           {'warning': _('YOU HAVE ALREADY CHECKED OUT.') % {'employee': self.name.split()[0]}}

            if last_attendance_obj.check_in_am and not last_attendance_obj.check_out_am:
                last_activity_time = last_attendance_obj.check_in_am
                my_action = 'check_out_am'

                if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                        last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):

                    return self and self.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                                  time_action=my_action, custom_action='no_action') or \
                           {'warning': _('YOU HAVE ALREADY CHECKED IN.') % {'employee': self.name.split()[0]}}

            if last_attendance_obj.check_in_pm and not last_attendance_obj.check_out_pm:
                last_activity_time = last_attendance_obj.check_in_pm
                my_action = 'check_out_pm'

                if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                        last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):

                    return self and self.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                                  time_action=my_action, custom_action='no_action') or \
                           {'warning': _('YOU HAVE ALREADY CHECKED IN.') % {'employee': self.name.split()[0]}}

        else:
            action_date = fields.Datetime.now()
            mid_day = datetime(2021, 01, 01, 12, 0, 0)
            hours = timedelta(hours=8)
            if (datetime.strptime(action_date, DEFAULT_SERVER_DATETIME_FORMAT) + hours).time() < mid_day.time():
                my_action = 'check_in_am'
            else:
                my_action = 'check_in_pm'

        if not (entered_pin is None) or self.env['res.users'].browse(SUPERUSER_ID).has_group(
                'zulu_attendance.group_hr_attendance_use_pin') and (
                self.user_id and self.user_id.id != self._uid or not self.user_id):
            if entered_pin != self.pin:
                return {'warning': _('Wrong PIN')}
        return self and self.attendance_action(next_action, time_action=my_action, custom_action=cust_action)

    @api.multi
    def attendance_action(self, next_action, time_action, custom_action="none"):
        """ Changes the attendance of the employee.
            Returns an action to the check in/out message,
            next_action defines which menu the check in/out message should return to. ("My Attendances" or "Kiosk Mode")
        """
        self.ensure_one()

        config = self.env['zulu_attendance.configuration'].search([], order='id desc', limit=1)
        action_message = self.env.ref('zulu_attendance.zulu_attendance_action_error_message').read()[0]
        action_message['previous_attendance_change_date'] = self.new_last_attendance_id and (
                self.new_last_attendance_id.check_out_am or self.new_last_attendance_id.check_in_pm
                or self.new_last_attendance_id.check_out_pm or self.new_last_attendance_id.check_in_am) or False
        action_message['employee_name'] = self.name
        action_message['next_action'] = next_action
        action_message['read_timeout'] = config.timeout
        action_message['time_action'] = time_action

        if self.user_id:
            modified_attendance = self.sudo(self.user_id.id).attendance_action_change()
            action_message['attendance'] = modified_attendance.read()[0]
        else:
            if custom_action != "no_action":
                modified_attendance = self.sudo().attendance_action_change()
                action_message['attendance'] = modified_attendance.read()[0]
        return {'action': action_message}

    @api.multi
    def attendance_action_change(self):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """

        if len(self) > 1:
            raise exceptions.UserError(_('Cannot perform check in or check out on multiple employees.'))
        action_date = fields.Datetime.now()
        now_date = datetime.now().date()
        from_date = datetime.strftime(now_date, '%Y-%m-%d 00:00:00')
        to_date = datetime.strftime(now_date, '%Y-%m-%d 23:59:00')
        attendance = self.env['hr_china.attendance'].search([('employee_id', '=', self.id), '&', '|',
                                                             ('check_in_am', '!=', False),
                                                             ('check_in_pm', '!=', False),
                                                             ('attendance_date', '>=', from_date),
                                                             ('attendance_date', '<=', to_date)], limit=1)

        if attendance:
            if attendance.check_in_am and not attendance.check_out_am:
                attendance.check_out_am = action_date
                return attendance
            if attendance.check_in_pm and not attendance.check_out_pm:
                attendance.check_out_pm = action_date
                return attendance

            if attendance.check_out_am and not attendance.check_in_pm:
                attendance.check_in_pm = action_date
                return attendance

        mid_day = datetime(2021, 01, 01, 12, 0, 0)
        hours = timedelta(hours=8)

        if (datetime.strptime(action_date, DEFAULT_SERVER_DATETIME_FORMAT) + hours).time() < mid_day.time():
            vals = {
                'employee_id': self.id,
                'check_in_am': action_date,
            }
            return self.env['hr_china.attendance'].create(vals)
        else:
            if attendance.check_in_am:
                vals = {
                    'employee_id': self.id,
                    'check_out_am': action_date,
                }
                return self.env['hr_china.attendance'].create(vals)

            vals = {
                'employee_id': self.id,
                'check_in_pm': action_date,
            }
            return self.env['hr_china.attendance'].create(vals)

        raise exceptions.UserError(
            _('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
              'Your attendances have probably been modified manually by human resources.') % {
                'empl_name': self.name, })
        return attendance


class HRNewAttendance(models.Model):
    _name = 'hr_china.attendance'
    _description = 'New Attendance Module'
    _order = 'attendance_date desc'

    attendance_date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True, store=True)
    attendance_day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], string='Day', compute='_get_day', store=True)
    check_in_am = fields.Datetime(string='Morning Check-In')
    check_out_am = fields.Datetime(string='Morning Check-Out')
    check_in_pm = fields.Datetime(string='Afternoon Check-In')
    check_out_pm = fields.Datetime(string='Afternoon Check-Out')
    break_hours = fields.Float(string='Break Hours', compute='_compute_break_hours')
    work_hours = fields.Float(string='Worked Hours', store=True, readonly=True, compute='_compute_worked_hours')
    overtime_hours = fields.Float(string='Overtime Hours', compute='_compute_overtime', default=0)

    check_in = fields.Datetime(string='Check In')
    check_out = fields.Datetime(string='Check Out')

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee, required=True,
                                  ondelete='cascade', index=True)

    @api.depends('check_in_am', 'check_out_am', 'check_in_pm', 'check_out_pm')
    def _compute_worked_hours(self):
        for attendance in self:
            morning_wh = False
            afternoon_wh = False
            if attendance.check_out_am and attendance.check_in_am:
                morning_wh_delta = datetime.strptime(attendance.check_out_am, DEFAULT_SERVER_DATETIME_FORMAT) - \
                                   datetime.strptime(attendance.check_in_am, DEFAULT_SERVER_DATETIME_FORMAT)
                morning_wh = morning_wh_delta.total_seconds() / 3600.0
            if attendance.check_out_pm and attendance.check_in_pm:
                afternoon_wh_delta = datetime.strptime(attendance.check_out_pm, DEFAULT_SERVER_DATETIME_FORMAT) - \
                                     datetime.strptime(attendance.check_in_pm, DEFAULT_SERVER_DATETIME_FORMAT)
                afternoon_wh = afternoon_wh_delta.total_seconds() / 3600.0

            if not morning_wh:
                morning_wh = 0
            if not afternoon_wh:
                afternoon_wh = 0

            total_wh = afternoon_wh + morning_wh
            attendance.work_hours = total_wh

    @api.onchange('check_in_pm')
    @api.depends('check_out_am', 'check_in_pm')
    def _compute_break_hours(self):
        for attendance in self:
            if attendance.check_out_am and attendance.check_in_pm:
                break_hours_delta = datetime.strptime(attendance.check_in_pm, DEFAULT_SERVER_DATETIME_FORMAT) - \
                                    datetime.strptime(attendance.check_out_am, DEFAULT_SERVER_DATETIME_FORMAT)
                attendance.break_hours = break_hours_delta.total_seconds() / 3600.0

    @api.depends('attendance_date')
    def _get_day(self):
        # return datetime.now().weekday()
        for attendance in self:
            attendance.attendance_day = str(datetime.now().weekday())

    @api.depends('work_hours')
    def _compute_overtime(self):
        for attendance in self:
            working_time = self.env['hr_china.employee_working_time'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('dayofweek', '=', attendance.attendance_day)
            ], order='id DESC')

            reg_hours = (working_time.hour_to - working_time.hour_from) - working_time.break_hours
            ot_hours = attendance.work_hours - reg_hours

            if ot_hours > 0:
                attendance.overtime_hours = ot_hours

    @api.multi
    def copy(self):
        raise exceptions.UserError(_('You cannot duplicate an attendance.'))

    @api.model
    def force_checkout_attendance(self):
        not_checkout = self.env['hr_china.attendance'].search(['|', ('check_out_am', '=', False),
                                                               ('check_out_pm', '=', False)])
        for rec in not_checkout:
            check_out_time = fields.Datetime.now()
            if rec.check_in_am and not rec.check_out_am:
                rec.check_out_am = check_out_time
            elif rec.check_in_pm and not rec.check_out_pm:
                rec.check_out_pm = check_out_time

