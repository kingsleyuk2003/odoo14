# -*- coding: utf-8 -*-

from odoo import api, fields, models

class survey_ticket_wizard(models.TransientModel):
    _name = 'survey.ticket.wizard'
    _description = 'Survey Ticket Wizard'

    
    def btn_survey_ticket(self):
        opp_id = self.env.context['active_id']
        msg = self.msg
        opp = self.env['crm.lead'].browse(opp_id)
        opp.action_create_survey_ticket(msg)
        return

    msg = fields.Text(string='Details', required=True)
