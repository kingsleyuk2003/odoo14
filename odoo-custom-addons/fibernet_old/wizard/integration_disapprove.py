# -*- coding: utf-8 -*-

from odoo import api, fields, models

class integration_disaaprove_wizard(models.TransientModel):
    _name = 'integration.disapprove.wizard'
    _description = 'Integration Disapprove Wizard'

    
    def disapprove_integration(self):
        tik_ids = self.env.context['active_ids']
        msg = self.msg
        tickets = self.env['kin.ticket'].browse(tik_ids)
        for ticket in tickets :
            ticket.action_ticket_reject(msg)
        return

    msg = fields.Text(string='Reason for Rejection', required=True)
