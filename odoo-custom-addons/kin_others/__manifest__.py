# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Other Modifications',
    'version': '0.1',
    'category': 'Others',
    'description': """
Other Miscelleaneous Modifications
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','mail','contacts','calendar'],
    'data': [
         'security/security.xml',
        'cron_data.xml',
        'others_view.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}