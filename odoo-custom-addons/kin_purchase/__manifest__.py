# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Purchase Modifications',
    'version': '1.2',
    'category': 'Inventory/Purchase',
    'sequence': 35,
    'description': "",
    'depends': ['purchase','purchase_stock','base_tier_validation'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/purchase_lines_report_wizard_view.xml',
        'views/report.xml',
        'views/purchase_views.xml',
        'views/purchase_order_tier_view.xml',

    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
