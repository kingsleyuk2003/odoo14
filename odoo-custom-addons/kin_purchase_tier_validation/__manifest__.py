# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
{
    'name': 'Purchase Order Tier Validation',
    'version': '0.1',
    'category': 'purchase',
    'description': """
Purchase order tier validation
=======================================================================================

""",
    'author': 'Kinsolve Solutions - kingsley@kinsolve.com',
    'website': 'http://kinsolve.com',
     'depends': ['base','base_tier_validation','purchase'],
    'data': [
        'data/purchase_order_tier_definition.xml',
        'views/purchase_order_view.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}