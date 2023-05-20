# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017-2022  Kinsolve Solutions
# Copyright 2017-2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Help Desk',
    'version': '0.1',
    'category': 'Sales',
    'description': """
HelpDesk
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','mail'],
    'data': [
        'security/helpdesk_security.xml',
        'security/ir.model.access.csv',
        'wizard/reassign_ticket_wizard.xml',
        'views/helpdesk_view.xml',
        'views/sequence.xml',
        'views/mail_template.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
}