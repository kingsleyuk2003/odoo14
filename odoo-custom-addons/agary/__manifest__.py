# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2024  Kinsolve Solutions
# Copyright 2024 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
{
    'name': 'Agary Modifications',
    'version': '0.1',
    'category': 'other',
    'description': """
Agary Modifications
=======================================================================================

""",
    'author': 'Kinsolve Solutions - kingsley@kinsolve.com',
    'website': 'http://kinsolve.com',
     'depends': ['base','kin_sales','kin_stock','mrp','stock_move_backdating','branch','kin_account_margin'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/stock.xml',
        'views/sale.xml',
        'views/account.xml',
        'views/mrp.xml',
        'views/branch_view.xml',
        'views/res_partner_view.xml',
        'views/report.xml',
        'report/report_invoice.xml',
        'report/report_deliveryslip.xml',
        'report/template.xml',
        'report/report_quote.xml',
        'wizard/sales_branch_wizard_view.xml',


    ],
    'test':[],
    'installable': True,
    'images': [],
}