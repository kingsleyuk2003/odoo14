# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2021  Kinsolve Solutions
# Copyright 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
{
    'name': 'Fibernet Modifications',
    'version': '0.1',
    'category': 'other',
    'description': """
Fibernet Modifications
=======================================================================================

""",
    'author': 'Kinsolve Solutions - kingsley@kinsolve.com',
    'website': 'http://kinsolve.com',
     'depends': ['base','sale','sale_management','mail','report_xlsx','kin_helpdesk','web_notify','kin_sales','kin_others','contract','kin_contract'],
    'data': [
        'data/data.xml',
        'report/report_invoice.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/report.xml',
        'views/res_config_settings_views.xml',
        'wizard/create_payment_entry.xml',
        'wizard/sales_order_disapprove.xml',
        'wizard/finalized_disapprove.xml',
        'wizard/ticket_report_wizard_view.xml',
        'wizard/installation_date_change.xml',
        'wizard/support_date_change.xml',
        'views/sequence.xml',
        'views/sale_view.xml',
        'views/ticket_view.xml',
        'views/contract.xml',
        'views/cron_data.xml',
        'views/audit_log.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}