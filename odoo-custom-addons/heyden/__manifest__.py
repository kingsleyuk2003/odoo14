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
     'depends': ['base','kin_loading'],
    'data': [
       'report/report_deliveryslip.xml',
        'report/report_loading_ticket.xml',
        'views/loading.xml',

    ],
    'test':[],
    'installable': True,
    'images': [],
}