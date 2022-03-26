# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AlertWizard(models.TransientModel):
    _name = 'alert.wizard'

    
    def action_alert(self):
        rec_ids = self.env.context['active_ids']
        msg = self.msg
        records = self.env['sale.order'].browse(rec_ids)
        for rec in records:
            rec.action_credit_limit_bypass_request(msg)
        return




