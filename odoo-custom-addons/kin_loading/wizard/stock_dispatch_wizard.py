# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import models, fields, api


class StockDispatchWizard(models.TransientModel):
    _name = 'stock.dispatch.wizard'

    #     def pdf_report(self, cr, uid, ids, context=None):
    #         context = context or {}
    #         datas = {'name':'PFS Report','ids': context.get('active_ids', [])} # use ids for pdf report otherwise there will be error
    #
    #         return {'type': 'ir.actions.report.xml',
    #                     'report_name': 'pfa.form.pdf.webkit',
    #                     'datas':datas,
    #                     }

    def stock_dispatch_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0]  # converts all objects to lists that can be easily be passed to the report
        data = {'name': 'Stock Dispatch Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'start_date': wiz_data['start_date'], 'type': wiz_data['type'],
                        'end_date': wiz_data['end_date'], 'product_ids': wiz_data['product_ids'],
                        'stock_dispatch_location_ids': wiz_data['stock_dispatch_location_ids'],
                        'partner_id': wiz_data['partner_id'], 'ticket_ids': wiz_data['ticket_ids'],
                        'waybill_no': wiz_data['waybill_no']}
        return self.env.ref('kin_loading.stock_dispatch_excel_report').report_action(self, data)

    name = fields.Char(string='Name')
    stock_dispatch_location_ids = fields.Many2many('stock.location', 'stock_dispatch_wizard_rel', 'stock_dispatch_wizard_id', 'stock_dispatch_loc_id', string='Stock Locations')
    product_ids = fields.Many2many('product.product', 'prod_stock_rel', 'stock_dispatch_wizard_id', 'stock_dispatch_loc_id',
                                   string='Products')
    start_date = fields.Date('Start Loaded Date')
    end_date = fields.Date('End Loaded Date')
    partner_id = fields.Many2one('res.partner', string='Customer')
    ticket_ids = fields.Many2many('stock.picking', string='Ticket(S)')
    waybill_no = fields.Char(string='Waybill')
    type = fields.Selection(
        [('is_indepot', 'In Depot'), ('is_throughput', 'Throughput'), ('is_internal_use', 'Internal Use'),
         ('all', 'All Operation Type')], string='Operation Type')






