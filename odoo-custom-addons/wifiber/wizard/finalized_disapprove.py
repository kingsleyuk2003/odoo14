# -*- coding: utf-8 -*-

from odoo import api, fields, models

class finalized_disaaprove_wizard(models.TransientModel):
    _name = 'finalized.disapprove.wizard'
    _description = 'finalized Disapprove Wizard'

    
    def disapprove_finalized(self):
        tik_ids = self.env.context['active_ids']
        msg = self.msg
        tickets = self.env['kin.ticket'].browse(tik_ids)
        for ticket in tickets :
            ticket.action_ticket_reject(msg)
        return

    msg = fields.Text(string='Reason for Rejection', required=True)
