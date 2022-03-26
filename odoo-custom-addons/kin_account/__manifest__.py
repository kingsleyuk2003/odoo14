# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Account Modifications',
    'version': '0.1',
    'category': 'Accounting',
    'description': """
Account Modifications
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','base_tier_validation' ,'account','kin_stock','kin_sales','kin_purchase','partner_statement'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/mail_data.xml',
        'wizard/activity_statement_wizard_extend.xml',
        'wizard/outstanding_statement_wizard_extend.xml',
        'wizard/alert_wizard.xml',
        'views/res_config_settings_views.xml',
        'report/custom_receipt.xml',
        'views/mail_template.xml',
        'views/account_view.xml',
        'views/account_payment_view.xml',
        'views/stock_view.xml',
        'views/account_move_tier_view.xml',
0
    ],
    'test':[],
    'installable': True,
    'images': [],
}