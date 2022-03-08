# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Purchase Modifications',
    'version': '1.2',
    'category': 'Inventory/Purchase',
    'sequence': 35,
    'description': "",
    'depends': ['purchase','purchase_stock'],
    'data': [
        'security/security.xml',
        'views/purchase_views.xml',

    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
