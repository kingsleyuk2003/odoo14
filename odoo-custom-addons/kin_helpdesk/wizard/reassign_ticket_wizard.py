# -*- coding: utf-8 -*-

from odoo import api, fields, models

class reassign_ticket_wizard(models.TransientModel):
    _name = 'reassign.ticket.wizard'
    _description = 'Reassign Ticket Wizard'

    def btn_reassign_ticket(self):
        ticket_id = self.env.context['active_id']
        ticket = self.env['kin.ticket'].browse(ticket_id)
        grp = self.user_ticket_group_id
        ticket.reassign_ticket(grp)
        return

    user_ticket_group_id = fields.Many2one('user.ticket.group',string='Ticket Group')
