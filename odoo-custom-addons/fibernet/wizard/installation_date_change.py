# -*- coding: utf-8 -*-

from odoo import api, fields, models

class installation_date_change_wizard(models.TransientModel):
    _name = 'installation.date.change.wizard'
    _description = 'Installation Date Change Wizard'

    
    def change_date(self):
        tik_ids = self.env.context['active_ids']
        new_installation_date = self.new_installation_date
        tickets = self.env['kin.ticket'].browse(tik_ids)
        for ticket in tickets :
            ticket.installation_date_change(new_installation_date)
        return

    new_installation_date = fields.Date(string='New Installation Date', required=True)
