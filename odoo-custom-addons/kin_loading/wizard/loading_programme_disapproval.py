# -*- coding: utf-8 -*-

from odoo import api, fields, models

class LoadingProgrammeDisApprovalWizard(models.TransientModel):
    _name = 'loading.programme.disapproval.wizard'
    _description = 'Loading Programme Disapproval Wizard'

    
    def action_disapprove(self):
        rec_ids = self.env.context['active_ids']
        msg = self.msg
        records = self.env['loading.programme'].browse(rec_ids)
        for rec in records:
            rec.action_disapprove(msg)
        return


    msg = fields.Text(string='Message', required=True)


