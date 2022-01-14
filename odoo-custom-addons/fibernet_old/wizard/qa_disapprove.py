# -*- coding: utf-8 -*-

from odoo import api, fields, models

class qa_disaaprove_wizard(models.TransientModel):
    _name = 'qa.disapprove.wizard'
    _description = 'QA Disapprove Wizard'

    
    def disapprove_qa(self):
        tik_ids = self.env.context['active_ids']
        msg = self.msg
        tickets = self.env['kin.ticket'].browse(tik_ids)
        for ticket in tickets :
            ticket.action_ticket_qa_reject(msg)
        return

    msg = fields.Text(string='Reason for Disapproval', required=True)
