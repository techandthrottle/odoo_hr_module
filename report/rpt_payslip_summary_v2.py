# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from pprint import pprint
from datetime import datetime
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from base64 import b64decode
from io import BytesIO
import re
import dateutil.parser
import json


class PayrollSummaryV2Xlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, ids):
        for id in ids:

            summary_trans = id.pslip_trans

            sheet = workbook.add_worksheet('Payroll Summary')

            sheet.set_portrait()
            sheet.fit_to_pages(1, 100)
            sheet.set_margins(left=0.25, right=0.25, top=0.4, bottom=0.4)

            sheet.set_column('A:A', 25)
            sheet.set_column('B:B', 25)
            sheet.set_column('C:C', 25)
            sheet.set_column('D:D', 25)
            sheet.set_column('E:E', 25)
            sheet.set_column('F:F', 25)
            sheet.set_row(0, 57)
            sheet.set_row(1, 21)
            sheet.set_row(2, 21)

            logo = self.env['hr_china.company_name_logo'].search([('is_active', '=', True)])

            format_logo = workbook.add_format({'bg_color': '#EEEEEE', 'top': 1, 'right': 1, 'bottom': 1})
            main_header_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'valign': 'vcenter',
                'align': 'center',
                'border': 1,
            })
            sub_header_format = workbook.add_format({
                'bold': True,
                'font_size': 11,
                'valign': 'vcenter',
                'align': 'center',
                'border': 1,
            })
            table_header_format = workbook.add_format({
                'bold': True,
                'font_size': 11,
                'valign': 'vcenter',
                'align': 'center',
                'border': 1,
            })
            left_content_format = workbook.add_format({
                'font_size': 11,
                'valign': 'vcenter',
                'align': 'left',
                'border': 1,
            })

            right_content_format = workbook.add_format({
                'font_size': 11,
                'valign': 'vcenter',
                'align': 'center',
                'border': 1,
                'num_format': 44,
            })

            center_content_format = workbook.add_format({
                'font_size': 11,
                'valign': 'vcenter',
                'align': 'center',
                'border': 1,
            })

            right_bottom_total_format = workbook.add_format({
                'font_size': 11,
                'valign': 'vcenter',
                'align': 'right',
                'top': 2,
                'bottom': 2,
                'num_format': 44,
            })

            right_bottom_content_format = workbook.add_format({
                'font_size': 11,
                'valign': 'vcenter',
                'align': 'right',
                'top': 2,
                'bottom': 2,
            })
            right_bottom_left_content_format = workbook.add_format({
                'font_size': 11,
                'valign': 'vcenter',
                'align': 'right',
                'top': 2,
                'bottom': 2,
                'left': 2,
            })
            right_bottom_right_content_format = workbook.add_format({
                'font_size': 11,
                'valign': 'vcenter',
                'align': 'right',
                'top': 2,
                'bottom': 2,
                'right': 2,
            })

            logo_bin64 = logo.logo

            if logo_bin64:
                logo_bytes_io = BytesIO(b64decode(re.sub("data:image/jpeg;base64", '', logo_bin64)))
                sheet.insert_image('C1', 'Company Logo',
                                   {'image_data': logo_bytes_io, 'y_offset': 3, 'x_offset': 150, 'x_scale': 0.10,
                                    'y_scale': 0.10})
            sheet.set_row(3, 21)
            sheet.merge_range('A1:F1', '', main_header_format)
            sheet.merge_range('A2:F2', 'PAYROLL SUMMARY', main_header_format)
            sheet.merge_range('A3:F3', id.name, sub_header_format)
            sheet.write('A4', 'Name', table_header_format)
            sheet.write('B4', 'Bank Name', table_header_format)
            sheet.write('C4', 'Branch', table_header_format)
            sheet.write('D4', 'Account Number', table_header_format)
            sheet.write('E4', 'Account Name', table_header_format)
            sheet.write('F4', 'Signature', table_header_format)
            s_row = 5
            row = 5
            for summary in summary_trans:
                sheet.set_row(row - 1, 30)
                emp_name = summary.name if summary.name else ''
                bank_name = summary.bank_name.name if summary.bank_name else ''
                bank_branch = summary.bank_branch if summary.bank_branch else ''
                account_number = summary.account_number if summary.account_number else ''
                account_name = summary.account_name if summary.account_name else ''

                sheet.write('A%s' % row, emp_name, left_content_format)
                sheet.write('B%s' % row, bank_name, center_content_format)
                sheet.write('C%s' % row, bank_branch, center_content_format)
                sheet.write('D%s' % row, account_number, center_content_format)
                sheet.write('E%s' % row, account_name, center_content_format)
                sheet.write('F%s' % row, '', center_content_format)
                row = row + 1
            sheet.set_row(row - 1, 21)
            sheet.write('A%s' % row, '', right_bottom_left_content_format)
            sheet.write('B%s' % row, '', right_bottom_total_format)
            sheet.write('C%s' % row, '', right_bottom_content_format)
            sheet.write('D%s' % row, '', right_bottom_content_format)
            sheet.write('E%s' % row, '', right_bottom_content_format)
            sheet.write('F%s' % row, '', right_bottom_right_content_format)


PayrollSummaryV2Xlsx('report.hr_china.payslip_summary_v2_xlsx', 'hr_china.payslip_summary')

