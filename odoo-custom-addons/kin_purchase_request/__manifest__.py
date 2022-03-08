# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Purchase Request Modifications',
    'version': '1.2',
    'category': 'Inventory/Purchase',
    'sequence': 35,
    'description': "",
    'depends': ['purchase_request'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/purchase_request_rejected.xml',
        'views/purchase_request_view.xml',


    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
