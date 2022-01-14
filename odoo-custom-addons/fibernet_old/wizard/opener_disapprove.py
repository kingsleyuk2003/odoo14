# -*- coding: utf-8 -*-

from odoo import api, fields, models

class opener_disaaprove_wizard(models.TransientModel):
    _name = 'opener.disapprove.wizard'
    _description = 'Ticket Opener Disapprove Wizard'

    
    def disapprove_opener(self):
        tik_ids = self.env.context['active_ids']
        msg = self.msg
        tickets = self.env['kin.ticket'].browse(tik_ids)
        for ticket in tickets :
            ticket.action_ticket_opener_reject(msg)
        return

    msg = fields.Text(string='Reason for Rejection', required=True)
