# -*- coding: utf-8 -*-

from odoo import api, fields, models

class expense_disaaprove_wizard(models.TransientModel):
    _name = 'expense.disapprove.wizard'
    _description = 'Expense Disapprove Wizard'

    
    def disapprove_expense(self):
        rec_ids = self.env.context['active_ids']
        msg = self.msg
        recs = self.env['hr.expense.group.kkon'].browse(rec_ids)
        for line in recs :
            line.action_expense_reject(msg)
        return

    msg = fields.Text(string='Reason for Rejection', required=True)
