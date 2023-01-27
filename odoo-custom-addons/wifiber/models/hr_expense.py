# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from datetime import datetime, timedelta
from odoo import SUPERUSER_ID
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from urllib.parse import urlencode
from urllib.parse import urljoin
import  time
from odoo import tools, api


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    def send_email(self, grp_name, subject, msg):
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref(grp_name)

        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)

        if partn_ids:
            # self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))


    def activity_update(self):
        return

    def reset_expense_sheets(self):
        if self.state == 'done':
            raise UserError('This Expense Sheet has been paid')
        return super(HrExpenseSheet, self).reset_expense_sheets()
    def refuse_sheet(self, reason):
        # check if payment has been made before
        if self.state == 'done':
            raise UserError('This Expense Sheet has been paid')

        # send email to requester
        user_id = self.employee_id.user_id
        partner_id = user_id.partner_id
        user_names = ''
        if partner_id:
            user_names += partner_id.name
            msg = 'Dear %s, <p>The expense (%s) has been  refused by %s, with reason: <br/> %s </p>' % (
                user_names, self.name, self.env.user.name,reason)
            self.message_follower_ids.unlink()
            mail_obj = self.message_post(
                body=_(msg),
                subject='Paid Expense Notification from %s' % (self.env.user.name),
                partner_ids=[partner_id.id],
                subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
        return super(HrExpenseSheet, self).refuse_sheet(reason)
    def paid_expense_sheets(self):
        # Not required, because it is called each time an expense line is approved, which raises an unwanted error
        # if self.state == 'done' :
        #     raise UserError('This Expense Sheet has been paid')

        # send email to requester
        user_id = self.employee_id.user_id
        partner_id = user_id.partner_id
        user_names = ''
        if partner_id:
            user_names += partner_id.name
            msg = 'Dear %s, <p>The expense (%s) has been paid by %s, to you</p>' % (
                user_names, self.name, self.env.user.name)
            self.message_follower_ids.unlink()
            mail_obj = self.message_post(
                body=_(msg),
                subject='Paid Expense Notification from %s' % (self.env.user.name),
                partner_ids=[partner_id.id],
                subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        return super(HrExpenseSheet, self).paid_expense_sheets()
    def audit_expense_sheets(self):
        # check if payment has been made before
        if self.state == 'done':
            raise UserError('This Expense Sheet has been paid')

        self.state = 'audited'

        # send email to Expense Accountants
        grp_name = 'wifiber.group_expense_account_application_wifiber'
        msg = 'The expense (%s) has been audited and approved by %s.  ' \
              'You can post entries and make payment </p>' % (
            self.name, self.env.user.name)
        subject = 'Audited and Approved Expense Notification to Post and Pay from %s' % (self.env.user.name)
        self.send_email(grp_name, subject, msg)

        # send email to requester
        user_id = self.employee_id.user_id
        partner_id = user_id.partner_id
        user_names = ''
        if partner_id:
            user_names += partner_id.name
            msg = 'Dear %s, <p>The expense (%s) has been audited by %s , and is awaiting payment to you.</p>' % (
                user_names, self.name, self.env.user.name)
            self.message_follower_ids.unlink()
            mail_obj = self.message_post(
                body=_(msg),
                subject='Audited and Approved Expense Notification from %s' % (self.env.user.name),
                partner_ids=[partner_id.id],
                subtype_xmlid='mail.mt_comment', force_send=False)


    def approve_expense_sheets(self):
        #send email to Auditors
        grp_name = 'wifiber.group_expense_auditor_wifiber'
        msg = 'The expense (%s) that has been approved by  %s, requires audit and approval </p>' % (
             self.name, self.env.user.name)
        subject = 'Expense Notification to Audit from %s' % (self.env.user.name)
        self.send_email(grp_name, subject, msg)

        #send email to requester
        user_id = self.employee_id.user_id
        partner_id = user_id.partner_id
        user_names = ''
        if partner_id:
            user_names += partner_id.name
            msg = 'Dear %s, <p>The expense (%s) has been approved by %s </p>' % (
                user_names, self.name, self.env.user.name)
            self.message_follower_ids.unlink()
            mail_obj = self.message_post(
                body=_(msg),
                subject='Approved Expense Notification from %s' % (self.env.user.name),
                partner_ids=[partner_id.id],
                subtype_xmlid='mail.mt_comment', force_send=False)

        return super(HrExpenseSheet,self).approve_expense_sheets()
    def action_submit_sheet(self):
        # check if payment has been made before
        if self.state == 'done':
            raise UserError('This Expense Sheet has been paid')

        #send email to the manager
        user_id = self.sudo()._get_responsible_for_approval()
        partner_id = user_id.partner_id
        user_names = ''
        if partner_id:
            user_names += partner_id.name
            msg = 'Dear %s, <p>There is a new expense (%s) from  %s to approve </p>' % (
                user_names,self.name, self.env.user.name)
            self.message_follower_ids.unlink()
            mail_obj = self.message_post(
                body=_(msg),
                subject='New Expense Notification to Approve from %s' % (self.env.user.name), partner_ids=[partner_id.id],
                subtype_xmlid='mail.mt_comment', force_send=False)

            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))


        return super(HrExpenseSheet,self).action_submit_sheet()


    def action_sheet_move_create(self):
        samples = self.mapped('expense_line_ids.sample')
        if samples.count(True):
            if samples.count(False):
                raise UserError(_("You can't mix sample expenses and regular ones"))
            self.write({'state': 'post'})
            return

        if any(sheet.state not in ('audited','approve') for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.company.currency_id).rounding))
        res = expense_line_ids.action_move_create()
        for sheet in self.filtered(lambda s: not s.accounting_date):
            sheet.accounting_date = sheet.account_move_id.date
        to_post = self.filtered(lambda sheet: sheet.payment_mode == 'own_account' and sheet.expense_line_ids)
        to_post.write({'state': 'post'})
        (self - to_post).write({'state': 'done'})
        self.activity_update()
        return res



    def _default_wifiber_bank_journal_id(self):
        return
        # default_company_id = self.default_get(['company_id'])['company_id']
        # return self.env['account.journal'].search([('type', 'in', ['cash', 'bank']),('company_id', '=', default_company_id), ('is_expense', '=', True) ], limit=1)

    payment_mode = fields.Selection(default='company_account')
    account_details = fields.Text(String='Account details')
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal',
                                      states={'done': [('readonly', True)], 'post': [('readonly', True)]},
                                      check_company=True,
                                      domain="[('type', 'in', ['cash', 'bank']), ('company_id', '=', company_id)]",
                                      default=_default_wifiber_bank_journal_id,
                                      help="The payment method used when the expense is paid by the company.")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('audited','Audited'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('cancel', 'Refused')
    ], string='Status', index=True, readonly=True, tracking=True, copy=False, default='draft', required=True,
        help='Expense Sheet Status')

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    def unlink(self):
        for rec in self:
            if rec.sheet_id and rec.sheet_id.state == 'audited':
                raise UserError('You are not allowed to delete an audited expense')
        return super(HrExpense, self).unlink()


    @api.depends('employee_id')
    def _compute_is_editable(self):
        is_account_manager = self.env.user.has_group('account.group_account_user') or self.env.user.has_group('account.group_account_manager') or self.env.user.has_group('wifiber.group_expense_account_application_wifiber')
        for expense in self:
            if expense.state == 'draft' or expense.sheet_id.state in ['draft', 'submit']:
                expense.is_editable = True
            elif expense.sheet_id.state in ('approve','audited'):
                expense.is_editable = is_account_manager
            else:
                expense.is_editable = False

    @api.depends('employee_id')
    def _compute_is_ref_editable(self):
        is_account_manager = self.env.user.has_group('account.group_account_user') or self.env.user.has_group('account.group_account_manager') or self.env.user.has_group('wifiber.group_expense_account_application_wifiber')
        for expense in self:
            if expense.state == 'draft' or expense.sheet_id.state in ['draft', 'submit']:
                expense.is_ref_editable = True
            else:
                expense.is_ref_editable = is_account_manager

    @api.depends('product_id', 'company_id')
    def _compute_from_product_id_company_id(self):
        for expense in self.filtered('product_id'):
            expense = expense.with_company(expense.company_id)
            expense.name = expense.name or expense.product_id.display_name
            expense.product_uom_id = expense.product_id.uom_id
            expense.tax_ids = expense.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == expense.company_id)  # taxes only from the same company
            account = expense.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account:
                expense.account_id = account

    def write(self, vals):
        if self.sheet_id and self.sheet_id.state == 'audited' and self.env.user.has_group('wifiber.group_expense_account_application_wifiber'):

            unit_amount = vals.get('unit_amount',False)
            date = vals.get('date', False)
            if unit_amount:
                raise UserError('Sorry, you not allowed to edit the Unit Price')
            if date:
                raise UserError('Sorry, you not allowed to edit the Expense Date')
        elif self.sheet_id and self.sheet_id.state == 'audited' and not self.env.user.has_group('wifiber.group_expense_auditor_wifiber'):
            raise UserError('You are not allowed to edit this expense')
        return super(HrExpense, self).write(vals)

    payment_mode = fields.Selection(default='company_account')
