# -*- coding: utf-8 -*-

from odoo import api, fields, models

class UnBlockTicketWizard(models.TransientModel):
    _name = 'unblock.ticket.wizard'


    
    def action_unblock_reason(self):
        rec_ids = self.env.context['active_ids']
        msg = self.msg
        records = self.env['stock.picking'].browse(rec_ids)
        for rec in records:
            rec.btn_unblock_ticket(msg)
        return


    msg = fields.Text(string='Reason for UnBlock', required=True)


