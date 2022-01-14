# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2021  Kinsolve Solutions
# Copyright 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import models, fields, api


class BankStatementWizard(models.TransientModel):
    _name = 'bank.statement.wizard'

    #     def pdf_report(self, cr, uid, ids, context=None):
    #         context = context or {}
    #         datas = {'name':'PFS Report','ids': context.get('active_ids', [])} # use ids for pdf report otherwise there will be error
    #
    #         return {'type': 'ir.actions.report.xml',
    #                     'report_name': 'pfa.form.pdf.webkit',
    #                     'datas':datas,
    #                     }


    def bank_statement_excel(self):
        context = self.env.context or {}
        data = {'name': 'Bank Statement Excel', 'active_ids': context.get('active_ids', [])}
        return self.env.ref('kin_bank_reconcile.action_bank_statement_xlsx').report_action(self,data=data)



