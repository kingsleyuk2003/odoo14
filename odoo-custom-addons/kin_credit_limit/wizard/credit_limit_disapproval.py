# -*- coding: utf-8 -*-

from odoo import api, fields, models

class CreditLimitDisApprovalWizard(models.TransientModel):
    _name = 'credit.limit.disapproval.wizard'
    _description = 'Credit Limit Disapproval Wizard'


    def action_credit_limit_disapprove(self):
        rec_ids = self.env.context['active_ids']
        msg = self.msg
        records = self.env['sale.order'].browse(rec_ids)
        for rec in records:
            rec.action_credit_limit_disapprove(msg)
        return


    msg = fields.Text(string='Reason', required=True)


