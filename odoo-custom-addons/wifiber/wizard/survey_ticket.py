# -*- coding: utf-8 -*-

from odoo import api, fields, models

class survey_ticket_wizard(models.TransientModel):
    _name = 'survey.ticket.wizard'
    _description = 'Survey Ticket Wizard'

    def btn_survey_ticket(self):
        opp_id = self.env.context['active_id']
        opp = self.env['crm.lead'].browse(opp_id)
        cmp_name = ''
        if opp.partner_name :
            cmp_name = "Customer: " + opp.partner_name
        details = opp.name + "\n" + cmp_name +  "\n" + "\n" +  "Address: " + opp.street + "\n" + "Phone: " + opp.phone + "\n" + "Email:" + opp.email_from
        msg = self.msg or ''
        opp.action_create_survey_ticket(details,msg)
        return

    msg = fields.Text(string='Other information')
