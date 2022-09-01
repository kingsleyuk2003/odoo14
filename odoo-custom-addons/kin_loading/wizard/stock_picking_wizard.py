# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import models, fields, api

class StockPickingWizard(models.TransientModel):
    _name = 'stock.picking.wizard'

    #     def pdf_report(self, cr, uid, ids, context=None):
    #         context = context or {}
    #         datas = {'name':'PFS Report','ids': context.get('active_ids', [])} # use ids for pdf report otherwise there will be error
    #
    #         return {'type': 'ir.actions.report.xml',
    #                     'report_name': 'pfa.form.pdf.webkit',
    #                     'datas':datas,
    #                     }

    
    def stock_picking_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0] #converts all objects to lists that can be easily be passed to the report
        data = {'name': 'Loading Ticket Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'states' : wiz_data['states'] , 'start_date' : wiz_data['start_date'], 'type':wiz_data['type'] ,'end_date':wiz_data['end_date'],'product_ids' : wiz_data['product_ids'],'partner_id' : wiz_data['partner_id'],'ticket_ids' : wiz_data['ticket_ids']}
        return self.env.ref('kin_loading.stock_picking_report').report_action(self, data)



    name = fields.Char(string='Name')
    ticket_ids = fields.Many2many('stock.picking',string='Ticket ID(s)')
    partner_id = fields.Many2one('res.partner', string='Customer')
    product_ids = fields.Many2many('product.product', 'stock_picking_loading_rel', 'stock_picking_wizard_id', 'prod_id', string='Products')
    start_date = fields.Datetime('Start Ticket Date')
    end_date = fields.Datetime('End Ticket Date')
    states = fields.Selection([
         ('done', 'Loaded'),
        ('not_done', 'Not Loaded')
    ], string='Status')
    type = fields.Selection(
        [('is_indepot', 'In Depot'), ('is_throughput', 'Throughput'), ('is_internal_use', 'Internal Use'),
         ('all', 'All Operation Type')], string='Operation Type')




