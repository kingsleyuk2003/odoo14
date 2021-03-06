# -*- coding: utf-8 -*-

from odoo import api, fields, models

class maint_disaaprove_wizard(models.TransientModel):
    _name = 'maint.disapprove.wizard'
    _description = 'Maintenance Disapprove Wizard'

    
    def disapprove_maint(self):
        tik_ids = self.env.context['active_ids']
        msg = self.msg
        tickets = self.env['kin.ticket'].browse(tik_ids)
        for ticket in tickets :
            ticket.action_ticket_maint_reject(msg)
        return

    msg = fields.Text(string='Reason for Declining', required=True)
