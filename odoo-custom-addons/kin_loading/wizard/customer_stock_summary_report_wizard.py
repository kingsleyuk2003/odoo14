# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import models, fields, api


class CustomerSummaryReportWizard(models.TransientModel):
    _name = 'customer.stock.summary.report.wizard'

    #     def pdf_report(self, cr, uid, ids, context=None):
    #         context = context or {}
    #         datas = {'name':'PFS Report','ids': context.get('active_ids', [])} # use ids for pdf report otherwise there will be error
    #
    #         return {'type': 'ir.actions.report.xml',
    #                     'report_name': 'pfa.form.pdf.webkit',
    #                     'datas':datas,
    #                     }

    
    def customer_stock_summary_excel_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0] #converts all objects to lists that can be easily be passed to the report
        data = {'name': 'Customer Stock Summary Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'partner_id' : wiz_data['partner_id'], 'type':wiz_data['type'],'product_ids' : wiz_data['product_ids']}
        return self.env.ref('kin_loading.customer_stock_summary_report').report_action(self, data)


    partner_id = fields.Many2one('res.partner',string='Customer')
    product_ids = fields.Many2many('product.product', 'customer_stock_summary_lines_rel', 'cust_stock_summary_wizard_id', 'prod_id', string='Products')
    type = fields.Selection(
        [('is_indepot', 'In Depot'), ('is_throughput', 'Throughput'), ('is_internal_use', 'Internal Use'),
         ('all', 'All Operation Type')], string='Operation Type')



