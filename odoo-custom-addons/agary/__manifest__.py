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
     'depends': ['base','kin_sales','kin_stock','mrp','stock_move_backdating'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/stock.xml',
        'views/sale.xml',
        'views/account.xml',
        'views/mrp.xml',
        #  'report/custom_report_layouts_agary.xml',
        # 'report/report_purchaseorder.xml',
        # 'report/custom_waybill_agary.xml',
        # 'report/custom_grn_agary.xml',
        # 'report/custom_invoice.xml',
        # 'report/custom_receipt.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}