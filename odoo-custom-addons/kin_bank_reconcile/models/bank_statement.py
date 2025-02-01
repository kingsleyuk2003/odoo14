# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2021  Kinsolve Solutions
# Copyright 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    
    def open_action(self):
        """return action based on type for related journals"""
        action_name = self._context.get('action_name', False)
        if not action_name:
            if self.type == 'bank':
                return self.view_bank_statement()
        return super(AccountJournal,self).open_action()


    
    def create_bank_statement(self):
        """return action to create a bank statements. This button should be called only on journals with type =='bank'"""
        self.bank_statements_source = 'manual'
        action = self.env.ref('kin_bank_reconcile.action_bank_statement').read()[0]
        action.update({
            'views': [[False, 'form']],
            'context': "{'default_journal_id': " + str(self.id) + "}",
        })
        return action




    
    def view_bank_statement(self):
        bank_statement_ids = self.mapped('bank_statement_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('kin_bank_reconcile.action_bank_statement')
        list_view_id = imd.xmlid_to_res_id('kin_bank_reconcile.bank_statement_tree')
        form_view_id = imd.xmlid_to_res_id('kin_bank_reconcile.bank_statement_form')

        result = {
                'name': action.name,
                'help': action.help,
                'type': action.type,
                'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                          [False, 'calendar'], [False, 'pivot']],
                'target': action.target,
                'context': action.context,
                'res_model': action.res_model,
                'target': 'current',
        }
        if len(bank_statement_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % bank_statement_ids.ids
        elif len(bank_statement_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = bank_statement_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    
    def get_journal_dashboard_datas(self):
        res = super(AccountJournal,self).get_journal_dashboard_datas()

        if self.type == 'bank':
            gl_balance = reconciled_bal = unreconciled_bal = 0
            account_ids = tuple(filter(None, [self.payment_debit_account_id.id, self.payment_credit_account_id.id]))
            if account_ids:
                amount_field = 'balance' if not self.currency_id else 'amount_currency'
                query = """SELECT sum(%s) FROM account_move_line WHERE account_id in %%s;""" % (amount_field,)
                self.env.cr.execute(query, (account_ids,))
                query_results = self.env.cr.dictfetchall()
                if query_results and query_results[0].get('sum') != None:
                    gl_balance = query_results[0].get('sum')

                query_reconciled = """SELECT sum(%s) FROM account_move_line WHERE is_bank_reconciled = 'True' and  account_id in %%s;""" % (amount_field,)
                self.env.cr.execute(query_reconciled, (account_ids,))
                query_results_reconciled = self.env.cr.dictfetchall()
                if query_results_reconciled and query_results_reconciled[0].get('sum') != None:
                    reconciled_bal = query_results_reconciled[0].get('sum')

                query_unreconciled = """SELECT sum(%s) FROM account_move_line WHERE is_bank_reconciled = 'False' and  account_id in %%s;""" % (
                amount_field,)
                self.env.cr.execute(query_unreconciled, (account_ids,))
                query_results_unreconciled = self.env.cr.dictfetchall()
                if query_results_unreconciled and query_results_unreconciled[0].get('sum') != None:
                    unreconciled_bal = query_results_unreconciled[0].get('sum')

            res.update({
                        'count_bank_statement' : len(self.bank_statement_ids),
                        'gl_balance' : formatLang(self.env, gl_balance, currency_obj=self.currency_id or self.company_id.currency_id),
                        'reconciled_bal' : formatLang(self.env, reconciled_bal, currency_obj=self.currency_id or self.company_id.currency_id),
                        'unreconciled_bal' : formatLang(self.env, unreconciled_bal, currency_obj=self.currency_id or self.company_id.currency_id),
                    }
                )
        return res

    bank_statement_ids = fields.One2many('bank.statement','journal_id',string='Statements')



class AccountMoveLineExtend(models.Model):
    _inherit = 'account.move.line'

    is_bank_reconciled = fields.Boolean(string='Reconciled')
    bank_statement_id  = fields.Many2one('bank.statement',string='Bank Statement')


class BankStatement(models.Model):
    _name = 'bank.statement'
    _inherit = ['mail.thread']

    
    def unlink(self):
        for rec in self:
            is_true = rec.move_line_ids.filtered(lambda line: line.is_bank_reconciled == True)
            if is_true:
                raise UserError(_('Please unreconcile each line to delete the statement'))

        return super(BankStatement, self).unlink()

    
    def action_create_entry_wizard(self):
        action = self.env['ir.model.data'].xmlid_to_object(
                'kin_bank_reconcile.action_create_entry')
        model_data_obj = self.env['ir.model.data']
        form_view_id = model_data_obj.xmlid_to_res_id(
                'kin_bank_reconcile.view_create_entry')

        return {
                'name': action.name,
                'help': action.help,
                'type': action.type,
                'views': [[form_view_id, 'form']],
                'target': action.target,
                'domain': action.domain,
                'context': {'default_bank_account_id': self.account_id.id},
                'res_model': action.res_model,
                'target': 'new'
            }


    def btn_print_pdf_statement(self):
        return self.env.ref('kin_bank_reconcile.action_report_bank_statement_pdf').report_action(self)

    def _compute_discrepancy(self):
        for rec in self:
            rec.qty_discrepancy = rec.quantity_loaded - rec.qty_received
            rec.product_price = rec.product_id.standard_price
            rec.amt_discrepancy = rec.product_id.standard_price * rec.qty_discrepancy



    def _compute_gl_balance(self):
        self.gl_balance = self.get_gl_balance()
        self._compute_reconcile()


    def get_gl_balance(self):
        journal_id = self.journal_id
        balance = 0
        if journal_id:
            account_ids = tuple(filter(None, [journal_id.payment_debit_account_id.id, journal_id.payment_credit_account_id.id]))
            if account_ids:
                amount_field = 'balance' if not journal_id.currency_id else 'amount_currency'
                query = """SELECT sum(%s) FROM account_move_line WHERE parent_state = 'posted' and date <= '%s' and account_id in %%s;""" % (amount_field,self.end_date,)
                self.env.cr.execute(query, (account_ids,))
                query_results = self.env.cr.dictfetchall()
                if query_results and query_results[0].get('sum') != None:
                    balance = query_results[0].get('sum')
        return balance

    @api.depends('journal_id')
    def _compute_account(self):
        journal_id = self.journal_id
        account = journal_id.payment_debit_account_id or journal_id.payment_credit_account_id
        self.account_id = account


    @api.depends('gl_balance','bank_reconciled_balance')
    def _compute_outstanding_amt(self):
        for rec in self:
            rec.outstanding_amt = rec.get_outstanding_checks()


    def get_outstanding_checks(self):
        journal_id = self.journal_id
        balance = 0
        if journal_id:
            account_ids = tuple(
                filter(None, [journal_id.payment_debit_account_id.id, journal_id.payment_credit_account_id.id]))
            if account_ids:
                amount_field = 'balance' if not journal_id.currency_id else 'amount_currency'
                query = """SELECT sum(Abs(%s)) FROM account_move_line WHERE parent_state = 'posted' and is_bank_reconciled = 'False' and date <= '%s' and account_id in %%s;""" % (
                amount_field, self.end_date,)
                self.env.cr.execute(query, (account_ids,))
                query_results = self.env.cr.dictfetchall()
                if query_results and query_results[0].get('sum') != None:
                    balance = query_results[0].get('sum')
        return balance

    def get_outstanding_amt(self):
        journal_id = self.journal_id
        balance = 0
        if journal_id:
            account_ids = tuple(
                filter(None, [journal_id.payment_debit_account_id.id, journal_id.payment_credit_account_id.id]))
            if account_ids:
                amount_field = 'balance' if not journal_id.currency_id else 'amount_currency'
                query = """SELECT sum(%s) FROM account_move_line WHERE parent_state = 'posted' and is_bank_reconciled = 'False' and date <= '%s' and account_id in %%s;""" % (
                amount_field, self.end_date,)
                self.env.cr.execute(query, (account_ids,))
                query_results = self.env.cr.dictfetchall()
                if query_results and query_results[0].get('sum') != None:
                    balance = query_results[0].get('sum')
        return balance


    @api.depends('statement_end_balance','outstanding_amt','move_line_ids.balance')
    def _compute_unreconcile(self):
        for rec in self:
            rec.unreconciled_balance = rec.gl_balance - rec.statement_end_balance - rec.get_outstanding_amt()

    @api.depends('move_line_ids.balance')
    def _compute_reconcile(self):
        ans = self.get_reconciled_amount()
        self.bank_reconciled_balance = ans

    def get_reconciled_amount(self):
        journal_id = self.journal_id
        reconcile_balance = 0
        if journal_id:
            amount_field = 'balance' if not journal_id.currency_id else 'amount_currency'
            account_ids = tuple(filter(None, [journal_id.payment_debit_account_id.id, journal_id.payment_credit_account_id.id]))
            query_reconciled = """SELECT sum(%s) FROM account_move_line WHERE parent_state = 'posted' and  is_bank_reconciled = 'True' and  account_id in %%s;""" % (
            amount_field,)
            self.env.cr.execute(query_reconciled, (account_ids,))
            query_results_reconciled = self.env.cr.dictfetchall()
            if query_results_reconciled and query_results_reconciled[0].get('sum') != None:
                reconcile_balance = query_results_reconciled[0].get('sum')
        return  reconcile_balance

    def btn_get_lines(self):
        self._compute_gl_balance()
        start_date = self.start_date
        end_date = self.end_date
        journal_id = self.journal_id
        account = journal_id.payment_debit_account_id or journal_id.payment_credit_account_id
        move_line_obj = self.env['account.move.line']
        for ml in self.move_line_ids:
            ml.is_bank_reconciled =  False
            ml.bank_statement_id = False
        domain = [('account_id','=',account.id),('is_bank_reconciled','=',False),('parent_state','=','posted')]
        if start_date:
            domain.append(('date', '>=',start_date))
        if end_date:
            domain.append(('date', '<=',end_date))
        move_lines = move_line_obj.search(domain)
        self.move_line_ids = [(6, 0,move_lines.ids)]



    def btn_check_all(self):
        for line in self.move_line_ids:
            line.is_bank_reconciled = True
        self._compute_unreconcile()

    def btn_uncheck_all(self):
        for line in self.move_line_ids:
            line.is_bank_reconciled = False
        self._compute_unreconcile()


    def btn_approve(self):
        if self.unreconciled_balance != 0 :
            raise UserError("Sorry, the Unreconciled Difference below should be Zero")
        self.state = 'approve'

    
    def btn_reset(self):
        self.state = 'draft'

    
    def btn_cancel(self):
        self.state = 'cancel'

    def btn_update(self):
        self._compute_gl_balance()


    @api.depends('journal_id')
    def _compute_currency(self):
        self.currency_id = self.journal_id.currency_id or self.company_id.currency_id

    name = fields.Char(string='Description')
    journal_id = fields.Many2one('account.journal',string='Bank Journal')
    account_id = fields.Many2one('account.account',string='Account',compute='_compute_account')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='Statement End Date')
    gl_balance = fields.Monetary(help='Balance as per Company Books',string='GL Balance',compute='_compute_gl_balance',store=True)
    bank_reconciled_balance = fields.Monetary(help='Balance as per Bank',string='Reconciled Balance',compute='_compute_reconcile',store=True)
    unreconciled_balance = fields.Monetary(help='Amounts not reflected in Bank',string='UNRECONCILED DIFFERENCE',compute='_compute_unreconcile',store=True)
    statement_end_balance = fields.Monetary(string="Statement Ending Balance")
    outstanding_amt = fields.Monetary(string="Outstanding Checks", help='Checks or Deposit in Transit', compute='_compute_outstanding_amt', store=True)
    currency_id = fields.Many2one('res.currency', compute='_compute_currency', string="Currency")
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', store=True,
                                 readonly=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'bank.statement'))
    move_line_ids = fields.One2many('account.move.line','bank_statement_id',string="Statement Lines")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled'),
    ], 'Status', default='draft',select=True, readonly=True, copy=False)


#
#
# class BankStatementLines(models.Model):
#     _name = 'bank.statement.line'
#
#
#
#     line_date = fields.Date(string='Date')
#     name = fields.Char(string='Description')
#     partner = fields.Many2one('res.partner',string='Partner')
#     statement_id = fields.Many2one('bank.statement', string='Statement', index=True, required=True,
#                                    ondelete='cascade')
#     journal_currency_id = fields.Many2one('res.currency', related='statement_id.currency_id',
#                                           help='Utility field to express amount currency', readonly=True)
#
#     amount = fields.Monetary(digits=0, currency_field='journal_currency_id')
#     journal_id = fields.Many2one('account.journal', related='statement_id.journal_id', string='Journal', store=True,
#                                  readonly=True)
#     reconciliation_account = fields.Many2one('account.account',string='Rec. Account')
#
#

