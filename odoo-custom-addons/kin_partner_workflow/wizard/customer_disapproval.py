# -*- coding: utf-8 -*-

from odoo import api, fields, models

class CustomerDisApprovalWizard(models.TransientModel):
    _name = 'customer.disapproval.wizard'
    _description = 'Customer Disapproval Wizard'


    def action_disapprove(self):
        rec_ids = self.env.context['active_ids']
        msg = self.msg
        records = self.env['res.partner'].browse(rec_ids)
        for rec in records:
            rec.action_disapprove(msg)
        return



    msg = fields.Text(string='Message', required=True)


