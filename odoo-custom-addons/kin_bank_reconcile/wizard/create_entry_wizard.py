# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2021  Kinsolve Solutions
# Copyright 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models
from odoo.tools.translate import _
from datetime import datetime, timedelta
from odoo.exceptions import UserError



class CreateEntryWizard(models.TransientModel):
    _name = 'create.entry.wizard'

    
    def btn_create_entry(self):
        rec_id = self.env.context['active_id']
        bank_statement_id = self.env['bank.statement'].browse(rec_id)

        bank_account_id = bank_statement_id.account_id
        journal_id = bank_statement_id.journal_id
        trx_type =self.trx_type
        counter_account_id = self.account_id
        partner_id = self.partner_id
        name = self.name
        ref = self.ref
        date = self.date
        amount = self.amount

        if not trx_type:
            raise UserError(_('Please select a Transaction Type'))

        if amount <= 0 :
            raise UserError(_('Please Set an Amount value that is greater than 0'))

        if counter_account_id.user_type_id.id == self.env.ref('account.data_account_type_receivable').id and not partner_id:
            raise UserError('Please Set the Partner Field for the Receivable Account')

        if counter_account_id.user_type_id.id == self.env.ref('account.data_account_type_payable').id and not partner_id:
            raise UserError('Please Set the Partner Field for the Payable Account')

        debit_account = credit_account = deb_stm_id = cr_stm_id = False
        if trx_type == 'increase':
            debit_account = bank_account_id
            credit_account = counter_account_id
            deb_stm_id =  bank_statement_id.id
        elif trx_type == 'decrease' :
            debit_account = counter_account_id
            credit_account = bank_account_id
            cr_stm_id = bank_statement_id.id

        mv_lines = []
        move_id = self.env['account.move'].create({
            'journal_id': journal_id.id,
            'company_id': self.env.user.company_id.id,
            'date': date
        })
        move_line = (0, 0, {
            'name': name.split('\n')[0][:64],
            'account_id': debit_account.id,
            'partner_id': partner_id.id,
            'debit': amount,
            'credit': 0,
            'ref': ref,
            'bank_statement_id' : deb_stm_id
        })
        mv_lines.append(move_line)

        move_line = (0, 0, {
            'name': name.split('\n')[0][:64],
            'account_id': credit_account.id,
            'partner_id': partner_id.id,
            'debit': 0,
            'credit': amount,
            'ref': ref,
            'bank_statement_id' : cr_stm_id
        })
        mv_lines.append(move_line)

        if mv_lines:
            move_id.write({'line_ids': mv_lines})
            move_id.post()

        #add to the Line

        return

    trx_type = fields.Selection([
        ('increase', 'Credit  - CREDIT the Account Selected Below and DEBIT the Bank on the Statement'),
        ('decrease', 'Debit - DEBIT the Account Selected Below and CREDIT the Bank on the Statement'),
    ], 'Transaction Type', select=True)
    account_id = fields.Many2one('account.account',string='Account')
    partner_id = fields.Many2one('res.partner',string='Partner')
    name = fields.Char(string='Description')
    ref = fields.Char(string='Reference')
    date = fields.Date(string='Date', default=lambda self: datetime.today())
    amount = fields.Float(string='Amount')
    bank_account_id = fields.Many2one('account.account',string='Bank Account')




