# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Credit Limit Workflow',
    'version': '0.1',
    'category': 'Sales',
    'description': """
Credit Limit Workflow
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['sale','kin_sales','web_notify'],
    'data': [
        'wizard/credit_limit_by_pass.xml',
        'wizard/credit_limit_disapproval.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/partner_view.xml',
        'views/sale_view.xml',
        'views/res_config_settings_views.xml',

    ],
    'test':[],
    'installable': True,
    'images': [],
}