# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2021  Kinsolve Solutions
# Copyright 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Accounting Contract Extension',
    'version': '0.1',
    'website': 'kinsolve.com',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'description': """
Accounting Contract Extension
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['account','contract'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}