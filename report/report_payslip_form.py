# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from base64 import b64decode
from io import BytesIO
import re
from pprint import pprint


class HRChinaPayslipFormRPT(models.AbstractModel):
    _name = 'report.hr_china.payslip_form'

    @api.model
    def render_html(self, payslip_id, data=None):
        company_id = self.env['hr_china.company_name_logo'].search([('is_active', '=', True)], limit=1, order='id DESC')
        payslip_data = self.env['hr_china.payslip'].browse(payslip_id[0])

        dict_data = {
            'company_id': company_id,
            'payslip_data': payslip_data,
            'data': data
        }

        return self.env['report'].render('hr_china.payslip_form', dict_data)


class HRChinaTimesheetFormRPT(models.AbstractModel):
    _name = 'report.hr_china.timesheet_form_rpt'

    @api.model
    def render_html(self, timesheet_id, data=None):
        company_id = self.env['hr_china.company_name_logo'].search([('is_active', '=', True)], limit=1, order='id DESC')
        timesheet_lis = self.env['hr_china.timesheet'].browse(timesheet_id[0])

        timesheet_attndnce = self.env['hr_china.attendance'].search(
            [('employee_id', '=', timesheet_lis.employee_id.id)], order='attendance_date ASC')

        dict_data = {
            'company_id': company_id,
            'timesheet_lis': timesheet_lis,
            'timesheet_attndnce': timesheet_lis.attendance_trans
        }

        return self.env['report'].render('hr_china.timesheet_form_rpt', dict_data)
