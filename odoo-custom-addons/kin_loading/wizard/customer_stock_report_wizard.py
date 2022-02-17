# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import models, fields, api


class CustomerStockReportWizard(models.TransientModel):
    _name = 'customer.stock.report.wizard'

    #     def pdf_report(self, cr, uid, ids, context=None):
    #         context = context or {}
    #         datas = {'name':'PFS Report','ids': context.get('active_ids', [])} # use ids for pdf report otherwise there will be error
    #
    #         return {'type': 'ir.actions.report.xml',
    #                     'report_name': 'pfa.form.pdf.webkit',
    #                     'datas':datas,
    #                     }

    
    def customer_stock_excel_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0] #converts all objects to lists that can be easily be passed to the report
        data = {'name': 'Customer Stock Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'partner_ids' : wiz_data['partner_ids'],'type':wiz_data['type'], 'product_ids' : wiz_data['product_ids']}
        return self.env.ref('kin_loading.customer_stock_report').report_action(self, data)


    partner_ids = fields.Many2many('res.partner', 'partner_stock_rel', 'partner_stock_wizard_id', 'partner_id', string='Customers')
    product_ids = fields.Many2many('product.product', 'customer_stock_rel', 'cust_stock_wizard_id', 'prod_id', string='Products')
    type = fields.Selection(
        [('is_indepot', 'In Depot'), ('is_throughput', 'Throughput'), ('is_internal_use', 'Internal Use'),
         ('all', 'All Operation Type')], string='Operation Type')



