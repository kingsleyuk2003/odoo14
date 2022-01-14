# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2021  Kinsolve Solutions
# Copyright 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Manual Bank Reconciliation',
    'version': '0.1',
    'website': 'kinsolve.com',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'description': """
Manual Bank Reconciliation 
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['account','report_xlsx'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
         'wizard/create_entry_view.xml',
        'wizard/bank_statement_wizard_view.xml',
        'views/kin_report.xml',
        'views/bank_statement_view.xml',
        'report/bank_statement_pdf.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}