# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Sales Modifications',
    'version': '0.1',
    'category': 'Sales',
    'description': """
Sales Modifications.
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['sale','sales_team','account','sale_management','base_tier_validation'],
    'data': [
        # 'wizard/create_advance_invoice.xml',
        'security/security.xml',

        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'views/partner_view.xml',
        'views/sale_view.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_tier_view.xml',
        'data/sequence.xml',
        'data/cron_data.xml',

    ],
    'test':[],
    'installable': True,
    'images': [],
}