# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, vals):
        # Check if credit limit has been approved
        credit_limit = vals.get('credit_limit', False)
        if credit_limit:
            vals.update({'is_credit_limit_changed': True, 'is_credit_limit_changed_by': self.env.user.id,
                         'is_credit_limit_approved': False, 'is_credit_limit_last_approved_by': False})
        res = super(ResPartner, self).create(vals)
        return res

    def write(self, vals):
        credit_limit = vals.get('credit_limit', False)
        if self and credit_limit:
            self.is_credit_limit_changed = True
            self.is_credit_limit_changed_by = self.env.user
            self.is_credit_limit_approved = False
            self.is_credit_limit_last_approved_by = False

            # notify superior for change
            partner_ids = []
            group_obj = self.env.ref('sales_team.group_sale_manager')
            user_names = ''
            for user in group_obj.users:
                user_names += user.partner_id.name + ", "
                partner_ids.append(user.partner_id.id)

            partner_names = ''
            partner_ids = []
            group_obj = self.env.ref('kin_credit_limit.group_receive_credit_limit_approval_notification')
            for user in group_obj.users:
                partner_ids.append(user.partner_id.id)
                partner_names += user.partner_id.name + ", "
            #TODO Causing error. check later
            # if partner_ids:
            #     subject = 'Credit Limit Field Changed for Partner'
            #     body = 'The credit limit field has been changed by %s, from %s to %s, for the partner %s' % (self.env.user.name, self.credit_limit, credit_limit, self.name)
            #     self.message_post(subject=subject, body=body, subtype_xmlid='mail.mt_comment', force_send=False, partner_ids=partner_ids)
            #     self.env.user.notify_info('%s Will Be Notified by Email' % (partner_names))

        res = super(ResPartner, self).write(vals)
        return res

    def btn_approve_credit_limit(self):
        self.is_credit_limit_changed = False
        self.is_credit_limit_changed_by = False
        self.is_credit_limit_approved = True
        self.is_credit_limit_last_approved_by = self.env.user

        partner_names = ''
        partner_ids = []
        group_obj = self.env.ref('kin_credit_limit.group_receive_request_credit_limit_bypass_notification')
        for user in group_obj.users:
            partner_ids.append(user.partner_id.id)
            partner_names += user.partner_id.name + ", "
        if partner_ids:
            subject = 'Credit Limit Field Approved for the Partner'
            body = 'The new credit limit (%s) has been approved by %s, for the partner %s' % (
              self.credit_limit, self.env.user.name, self.name)
            self.message_post(subject=subject, body=body, subtype_xmlid='mail.mt_comment', force_send=False, partner_ids=partner_ids)
            self.env.user.notify_info('%s Will Be Notified by Email' % (partner_names))

    # Reference: odoo community aged partner code for getting due amount
    def _get_not_due_amount_receivable(self):
        for partner in self :
            cr = self.env.cr
            partner_id = partner.id
            move_state = 'posted'
            account_type = 'receivable'
            date_from = fields.Datetime.now()
            user_company = self.env.user.company_id.id
            future_past = 0
            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state = %s)
                        AND (account_account.internal_type = %s)
                        AND (COALESCE(l.date_maturity,l.date) > %s)\
                        AND (l.partner_id = %s)
                    AND (l.date <= %s)
                    AND l.company_id = %s'''
            cr.execute(query, (move_state,account_type, date_from, partner_id, date_from, user_company))
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                line_amount = line.balance
                if line.balance == 0:
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.create_date <= date_from:
                        line_amount += partial_line.amount
                for partial_line in line.matched_credit_ids:
                    if partial_line.create_date <= date_from:
                        line_amount -= partial_line.amount
                future_past += line_amount
            partner.not_due_amount_receivable = future_past

    def _get_due_amount_receivable(self):
        for partner in self:
            partner.due_amount_receivable = partner.credit - partner.not_due_amount_receivable


    def _get_allowed_credit(self):
        for partner in self:
            allowed_credit = partner.credit_limit - partner.due_amount_receivable
            if allowed_credit < 0 :
                partner.allowed_credit = 0
            else :
                partner.allowed_credit = allowed_credit


    name = fields.Char(tracking=True)
    credit_limit = fields.Monetary(string='Credit Limit')
    is_enforce_credit_limit_so = fields.Boolean(string='Activate Credit Limit')
    due_amount_receivable = fields.Monetary(string='Due',compute=_get_due_amount_receivable,help='Receivables that are Due to be paid')
    not_due_amount_receivable = fields.Monetary(string='Not Due',compute=_get_not_due_amount_receivable,help='Receivables that are Not Due to be Paid')
    allowed_credit = fields.Float(string='Remaining Credit Allowed',compute=_get_allowed_credit,help='Credit Allowance for the partner')
    is_credit_limit_changed = fields.Boolean(string="Is Credit Limit Changed") # no need to track visibilty on this fields, since it generates error for the partner model, when editing access right for users i.e. AttributeError: 'res.users' object has no attribute 'in_group_120
    is_credit_limit_changed_by = fields.Many2one('res.users', string='Credit Limit Changed User')
    is_credit_limit_approved = fields.Boolean(string="Is Credit Limit Approved",default=True)
    is_credit_limit_last_approved_by = fields.Many2one('res.users', string='Credit Limit Last Approved User')
