# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CreditLimitByPassWizard(models.TransientModel):
    _name = 'credit.limit.bypass.wizard'
    _description = 'Credit Limit By Pass'

    
    def action_credit_limit_bypass_request(self):
        rec_ids = self.env.context['active_ids']
        msg = self.msg
        records = self.env['sale.order'].browse(rec_ids)
        for rec in records:
            rec.action_credit_limit_bypass_request(msg)
        return

    msg = fields.Text(string='Reason', required=True)
    err_msg = fields.Char(string='Error Message:')


