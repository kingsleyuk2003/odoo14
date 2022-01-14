# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import models, fields, api


class LoadingProgrammeWizard(models.TransientModel):
    _name = 'loading.programme.wizard'

    #     def pdf_report(self, cr, uid, ids, context=None):
    #         context = context or {}
    #         datas = {'name':'PFS Report','ids': context.get('active_ids', [])} # use ids for pdf report otherwise there will be error
    #
    #         return {'type': 'ir.actions.report.xml',
    #                     'report_name': 'pfa.form.pdf.webkit',
    #                     'datas':datas,
    #                     }

    
    def loading_programme_excel(self):
        context = self.env.context or {}
        data = {'name': 'Loading Programme Excel', 'active_ids': context.get('active_ids', [])}
        return {
                    'name':'Loading Programme Export',
                    'type': 'ir.actions.report.xml',
                    'report_name': 'kin_loading.report_loading_programme_excel',
                    'datas': data, #It is required you use datas as parameter, otherwise it will transfer data correctly.
                    }



