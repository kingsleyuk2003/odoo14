# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
{
    'name': 'Heyden Modifications',
    'version': '0.1',
    'category': 'other',
    'description': """
Heyden Modifications
=======================================================================================

""",
    'author': 'Kinsolve Solutions - kingsley@kinsolve.com',
    'website': 'http://kinsolve.com',
     'depends': ['base','kin_loading','hr','hr_holidays','hr_contract','hr_employee_firstname','hr_employee_lastnames','stock_request','purchase_request','purchase_order_secondary_unit','kin_purchase','kin_stock','kin_sales','purchase_stock','account'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
       'report/report_deliveryslip.xml',
       'report/report_loading_ticket.xml',
        'report/report_invoice.xml',
       'wizard/sales_atl_wizard_view.xml',
        'views/report.xml',
       'views/loading.xml',
        'views/hr.xml',

    ],
    'test':[],
    'installable': True,
    'images': [],
}