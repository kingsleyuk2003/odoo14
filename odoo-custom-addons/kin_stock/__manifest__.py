# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Stock Modifications',
    'version': '0.1',
    'category': 'Warehouse',
    'description': """
Stock Extra Customization
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base_tier_validation','stock','stock_account','purchase','sale','sale_stock','account','stock_landed_costs'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/picking_rejected.xml',
        'wizard/stock_backorder_confirmation.xml',
        'wizard/stock_immediate_transfer_views.xml',
        'data/mail_template.xml',
        'views/stock_view.xml',
        'views/stock_tier_view.xml',
        'views/res_config_settings_views.xml',


    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'images': [],
}