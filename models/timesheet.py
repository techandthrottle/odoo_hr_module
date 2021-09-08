# -*- coding: utf-8 -*-

import math
from odoo import models, fields, api, exceptions, _, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta, date, time
from odoo.exceptions import UserError, AccessError, ValidationError
import time

from pprint import pprint


class HRTimesheet(models.Model):
    _name = "hr_china.timesheet"


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

        # Duplicate fix: no scan for the same person within specified secs ###
        last_attendance_obj = self.env['hr_china.attendance'].search([
            ('employee_id', '=', employee.id)
        ], order='id desc', limit=1)

        if last_attendance_obj.check_out_pm:
            last_activity_time = last_attendance_obj.check_out_pm
            my_action = 'check_in_am'
            if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                    last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):
                return employee and employee.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                                               time_action='check_out_pm', custom_action='no_action') or \
                       {'warning': _('YOU HAVE ALREADY CHECKED OUT.') % {'employee': employee.name.split()[0]}}

        if last_attendance_obj.check_in_pm:
            last_activity_time = last_attendance_obj.check_in_pm
            my_action = 'check_out_pm'
            if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                    last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):
                return employee and employee.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                                               time_action="check_in_pm", custom_action='no_action') or \
                       {'warning': _('YOU HAVE ALREADY CHECKED IN.') % {'employee': employee.name.split()[0]}}

        if last_attendance_obj.check_out_am:
            last_activity_time = last_attendance_obj.check_out_am
            my_action = 'check_in_pm'
            if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                    last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):
                return employee and employee.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                                               time_action="check_out_am", custom_action='no_action') or \
                       {'warning': _('YOU HAVE ALREADY CHECKED OUT.') % {'employee': employee.name.split()[0]}}

        if last_attendance_obj.check_in_am:
            last_activity_time = last_attendance_obj.check_in_am
            my_action = 'check_out_pm'
            if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                    last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):
                return employee and employee.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                                               time_action="check_in_am", custom_action='no_action') or \
                       {'warning': _('YOU HAVE ALREADY CHECKED IN.') % {'employee': employee.name.split()[0]}}
        # End of fix

        return employee and employee.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                                       time_action=my_action) or \
               {'warning': _('No employee corresponding to barcode %(barcode)s') % {'barcode': barcode}}

    @api.multi
    def attendance_manual(self, next_action, entered_pin=None):
        self.ensure_one()

        config = self.env['zulu_attendance.configuration'].search([], order='id desc', limit=1)
        last_attendance_obj = self.env['hr_china.attendance'].search([
            ('employee_id', '=', self.id)
        ], order='id desc', limit=1)

        my_action = False

        if last_attendance_obj.check_out_pm:
            last_activity_time = last_attendance_obj.check_out_pm
            my_action = 'check_in_am'
            if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                    last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):
                return self.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                              time_action="check_out_pm", custom_action='no_action') or \
                       {'warning': _('YOU HAVE ALREADY CHECKED OUT.') % {'employee': self.name.split()[0]}}

        if last_attendance_obj.check_in_pm:
            last_activity_time = last_attendance_obj.check_in_pm
            my_action = 'check_out_pm'
            if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                    last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):
                return self.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                              time_action="check_in_pm", custom_action='no_action') or \
                       {'warning': _('YOU HAVE ALREADY CHECKED IN.') % {'employee': self.name.split()[0]}}

        if last_attendance_obj.check_out_am:
            last_activity_time = last_attendance_obj.check_out_am
            my_action = 'check_in_pm'
            if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                    last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):
                return self.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                              time_action="check_out_am", custom_action='no_action') or \
                       {'warning': _('YOU HAVE ALREADY CHECKED OUT.') % {'employee': self.name.split()[0]}}

        if last_attendance_obj.check_in_am:
            last_activity_time = last_attendance_obj.check_in_am
            my_action = 'check_out_pm'
            if (datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                    last_activity_time, DEFAULT_SERVER_DATETIME_FORMAT)).seconds < (config.timeout * 60):
                return self.attendance_action('zulu_attendance.zulu_attendance_action_kiosk_mode',
                                              time_action="check_in_am", custom_action='no_action') or \
                       {'warning': _('YOU HAVE ALREADY CHECKED IN.') % {'employee': self.name.split()[0]}}

        if not (entered_pin is None) or self.env['res.users'].browse(SUPERUSER_ID).has_group(
                'zulu_attendance.group_hr_attendance_use_pin') and (
                self.user_id and self.user_id.id != self._uid or not self.user_id):
            if entered_pin != self.pin:
                return {'warning': _('Wrong PIN')}

        return self.attendance_action(next_action, time_action=my_action)

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
                or self.new_last_attendance_id.check_out_pm) or False
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

        attendance = self.env['hr_china.attendance'].search(['|', ('employee_id', '=', self.id),
                                                             ('check_in_am', '!=', False),
                                                             ('check_in_pm', '!=', False)], limit=1)

        if not attendance.check_out_am and not attendance.check_in_pm:
            attendance.check_out_am = action_date
            return attendance
        if not attendance.check_in_pm:
            attendance.check_in_pm = action_date
            return attendance
        if not attendance.check_out_pm:
            attendance.check_out_pm = action_date
            return attendance

        mid_day = datetime(2021, 01, 01, 12, 0, 0)
        hours = timedelta(hours=8)

        if (datetime.strptime(action_date, DEFAULT_SERVER_DATETIME_FORMAT) + hours).time() < mid_day.time():
            vals = {
                'employee_id': self.id,
                'check_in_am': action_date,
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

    attendance_date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    attendance_day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], string='Day', compute='_get_day')
    check_in_am = fields.Datetime(string='Morning Check-In')
    check_out_am = fields.Datetime(string='Morning Check-Out')
    check_in_pm = fields.Datetime(string='Afternoon Check-In')
    check_out_pm = fields.Datetime(string='Afternoon Check-Out')
    break_hours = fields.Float(string='Break Hours', compute='_compute_break_hours')
    work_hours = fields.Float(string='Worked Hours', store=True, readonly=True, compute='_compute_worked_hours')
    overtime_hours = fields.Float(string='Overtime Hours', compute='_compute_overtime', default=0)

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
                ('employee_id', '=', attendance.employee_id),
                ('dayofweek', '=', attendance.attendance_day)
            ], order='id DESC')

            reg_hours = (working_time.hour_to - working_time.hour_from) - working_time.break_hours
            ot_hours = attendance.work_hours - reg_hours
            if ot_hours > 0:
                attendance.overtime_hours = ot_hours

    @api.multi
    def copy(self):
        raise exceptions.UserError(_('You cannot duplicate an attendance.'))
