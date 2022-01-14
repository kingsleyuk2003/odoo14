# -*- coding: utf-8 -*-

from odoo import api, fields, models

class BlockTicketWizard(models.TransientModel):
    _name = 'block.ticket.wizard'


    
    def action_block_reason(self):
        rec_ids = self.env.context['active_ids']
        msg = self.msg
        records = self.env['stock.picking'].browse(rec_ids)
        for rec in records:
            rec.btn_block_ticket(msg)
        return


    msg = fields.Text(string='Reason for Block', required=True)


