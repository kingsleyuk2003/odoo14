# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2021  Kinsolve Solutions
# Copyright 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
{
    'name': 'Fibernet Modifications',
    'version': '0.1',
    'description': """
KKON Modifications
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com)',
    'depends': ['base','sale','mail','report_xlsx','kin_helpdesk','web_notify','crm','kin_sales'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'kkon_report.xml',
        'wizard/sales_order_disapprove.xml',
        'wizard/integration_disapprove.xml',
        'wizard/crm_wizard_view.xml',
        'wizard/qa_disapprove.xml',
        'wizard/opener_disapprove.xml',
        'wizard/maint_disapprove.xml',
        'wizard/survey_ticket.xml',
        'wizard/expense_disapprove.xml',
        'wizard/ticket_report_wizard_view.xml',
        'wizard/create_payment_entry.xml',
        'report/custom_report_layouts.xml',
        'report/custom_invoice.xml',
        'report/custom_receipt.xml',
        'account_view.xml',
        'data.xml',
        'cron_data.xml',
        'mail_template.xml',
        'sequence.xml',
        'sale_view.xml',
        'ticket_view.xml',
        'crm_view.xml',
        'hr_view.xml',
        'hr_expense_view.xml',
        'res_company.xml',
    ],
    'installable': True,
    'images': [],
}