# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Nexium Modifications',
    'version': '1.1',
    'summary': 'Nexium Modifications',
    'description': """
Nexium Modifications
    """,
    'depends': ['sale', 'kin_stock'],
    'data': [
        'security/nexium_security.xml',
        'security/ir.model.access.csv',
        'report/report_invoice.xml',
        'report/report_deliveryslip.xml',
        'report/report_release_order.xml',
        'report/report_tank_to_tank.xml',
        'data/ir_sequence_data.xml',
        'data/sale_data.xml',
        'views/res_config_settings_views.xml',
        'views/stock_view.xml',
        'views/account_move_views.xml',
        'views/res_partner_view.xml',
        'views/product_view.xml',
        'views/stock_view.xml',
        'views/sale_view.xml',
    ],
    'installable': True,
    'auto_install': False
}
