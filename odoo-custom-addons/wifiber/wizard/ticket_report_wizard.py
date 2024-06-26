# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2020  Kinsolve Solutions
# Copyright 2020 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import models, fields, api
import time


class TicketReportWizard(models.TransientModel):
    _name = 'ticket.wizard'

    
    def ticket_excel_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0]  # converts all objects to lists that can be easily be passed to the report
        data = {'name': 'Ticket Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'start_date': wiz_data['start_date'], 'end_date': wiz_data['end_date'],
                        'category_id':wiz_data['category_id'],'company_id':wiz_data['company_id']}
        return self.env.ref('wifiber.ticket_report').report_action(self,data)


    start_date = fields.Datetime('Start Date and Time', default=time.strftime('%Y-%m-01'))
    end_date = fields.Datetime('End Date and Time', default=fields.Datetime.now())
    category_id = fields.Many2one('kin.ticket.category',string='Ticket Category')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)



