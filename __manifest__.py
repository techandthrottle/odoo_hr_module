# -*- coding: utf-8 -*-
{
    'name': "HR China",

    'summary': """
        China's HR Module""",

    'description': """
        Long description of module's purpose
    """,

    'author': "1000 Miles",
    'website': "http://www.1000miles.biz",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
        'depends': ['base', 'calendar', 'hr', 'hr_holidays', 'zulu_attendance', ],

    'css': [
            'static/src/lib/jquery.timepicker.css',
            'static/src/css/style.css',
        ],

    'js': [
        'static/src/lib/jquery.timepicker.js',
        'static/src/js/web_widget_timepicker.js',
        'static/src/js/edit_btn.js',
        ],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/attendance_reports.xml',
        'report/rpt_payslip_form.xml',
        'report/rpt_timesheet_form.xml',
        'views/hr_china.xml',
        'views/attendance.xml',
        'views/time_setup.xml',
        'views/contract_setup.xml',
        'views/company_setup.xml',
        'views/employee.xml',
        'views/employee_contract.xml',
        'views/configuration.xml',
        'views/timesheet.xml',
        'views/payroll.xml',
        'views/views.xml',
        'views/templates.xml',
        ],

    'qweb': [
        'static/src/xml/web_widget_timepicker.xml',
        ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}