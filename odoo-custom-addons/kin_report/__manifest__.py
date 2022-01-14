# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Common Reports Modifications',
    'version': '0.1',
    'category': 'report',
    'description': """
Report Modifications
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['operating_unit'],
    'data': [
         'report/kin_report.xml',
        'report/custom_report_layouts.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}