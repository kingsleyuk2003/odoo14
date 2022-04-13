# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrderExtend(models.Model):
    _inherit = "sale.order"


    def action_credit_limit_bypass_request(self, msg):
        self.state = 'credit_limit_by_pass_request'
        self.credit_limit_bypass_requested_by_id = self.env.user.id
        self.bypass_msg = msg

        self.message_unsubscribe(partner_ids=[self.partner_id.id])
        partner_ids = []
        partner_names = ''
        group_obj = self.env.ref('kin_credit_limit.group_receive_request_credit_limit_bypass_notification')
        for user in group_obj.users:
            partner_ids.append(user.partner_id.id)
            partner_names += user.partner_id.name + ", "

        if partner_ids :
            subject = 'A New Credit Limit Request By Pass for the sales order has been requested'
            body = _('A New Credit Limit Request By Pass for the sales order %s has been requested from %s and needs your confirmation.') % (self.name, self.env.user.name)
            self.message_post(subject=subject, body=body, subtype_xmlid='mail.mt_comment', force_send=False, partner_ids=partner_ids,)
            self.env.user.notify_info('%s Will Be Notified by Email' % (partner_names))


    def confirm_credit_limit_bypass(self):
        self.state = 'credit_limit_by_pass_confirm'
        self.credit_limit_bypass_confirmed_by_id = self.env.user.id

        self.message_unsubscribe(partner_ids=[self.partner_id.id])  # to prevent the partner from receiving email
        partner_ids = []
        partner_names = ''
        group_obj = self.env.ref('kin_credit_limit.group_receive_confirm_credit_limit_bypass_notification')
        for user in group_obj.users:
            partner_ids.append(user.partner_id.id)
            partner_names += user.partner_id.name + ", "
        if partner_ids:
            subject = 'The Credit Limit Request By Pass for the sales order has been confirmed'
            body =  'The Credit Limit Request By Pass for the sales order %s has been confirmed by %s.' % (self.name,self.env.user.name)
            self.message_post(subject=subject,body=body,subtype_xmlid='mail.mt_comment', force_send=False,partner_ids=partner_ids)
            self.env.user.notify_info('%s Will Be Notified by Email' % (partner_names))

    def action_approve(self):
        res = super(SaleOrderExtend, self).action_confirm()
        return res

    def approve_credit_limit_bypass(self):
        self.credit_limit_bypass_approved_by_id = self.env.user.id
        # self.state = 'credit_limit_by_pass_approve' # no need for this. since anyway the action_approve() will change the state to sales order approved
        self.is_credit_limit_bypass = True
        self.action_approve()

        self.message_unsubscribe(partner_ids=[self.partner_id.id])
        partner_ids = []
        partner_names = ''
        group_obj = self.env.ref('kin_credit_limit.group_receive_approve_credit_limit_bypass_notification')
        for user in group_obj.users:
            partner_ids.append(user.partner_id.id)
            partner_names += user.partner_id.name + ", "
        if partner_ids:
            subject = 'The Credit Limit Request By Pass for the sales order has been finally approved'
            body = 'The Credit Limit Request By Pass for the sales order %s has been finally approved by %s.' % (self.name, self.env.user.name)
            self.message_post(subject=subject, body=body, subtype_xmlid='mail.mt_comment', force_send=False, partner_ids=partner_ids)
            self.env.user.notify_info('%s Will Be Notified by Email' % (partner_names))


    
    def action_credit_limit_disapprove(self, msg):
        self.bypass_msg_disapproved = msg
        self.is_credit_limit_bypass = False
        self.state = 'credit_limit_by_pass_disapprove'

        self.message_unsubscribe(partner_ids=[self.partner_id.id])
        partner_ids = []
        partner_names = ''
        group_obj = self.env.ref('kin_credit_limit.group_receive_disapprove_credit_limit_bypass_notification')
        for user in group_obj.users:
            partner_ids.append(user.partner_id.id)
            partner_names += user.partner_id.name + ", "
        if partner_ids:
            subject = 'The Credit Limit Request By Pass for the sales order has disapproved'
            body = 'The Credit Limit Request By Pass for the sales order %s has been disapproved by %s.' % (self.name, self.env.user.name)
            self.message_post(subject=subject, body=body, subtype_xmlid='mail.mt_comment', force_send=False, partner_ids=partner_ids)
            self.env.user.notify_info('%s Will Be Notified by Email' % (partner_names))

    
    def cancel_credit_limit_bypass(self):
        self.state = 'credit_limit_by_pass_cancel'
        self.is_credit_limit_bypass = False

    def action_confirm(self):
        customer = self.partner_id

        # Check if partner credit limit has been approved
        if customer:
            if customer.is_credit_limit_changed and not customer.is_credit_limit_approved:
                raise UserError(
                    _(
                        'Please Contact the Responsible User to Approve the New Credit Limit (%s), for the Partner (%s)') % (
                        customer.credit_limit, customer.name))

            # Credit limit Check
            if customer.is_enforce_credit_limit_so and not self.is_credit_limit_bypass:
                if not customer.is_credit_limit_approved:
                    raise UserError('%s credit limit is yet to be approved' % (customer.name))

                if self.amount_total > customer.allowed_credit:
                        # Show the wizard to by-pass or display message
                        model_data_obj = self.env['ir.model.data']
                        action = self.env['ir.model.data'].xmlid_to_object(
                            'kin_credit_limit.action_credit_limit_bypass').sudo()
                        form_view_id = model_data_obj.xmlid_to_res_id(
                            'kin_credit_limit.view_credit_limit_bypass')

                        err_msg = 'Total Sales Amount %s%s has exceeded the remaining credit %s%s for %s. You may request for credit limit by pass for this sales order with a reason.' % (
                        self.currency_id.symbol, self.amount_total, self.currency_id.symbol, customer.allowed_credit,
                        customer.name)
                        return {
                            'name': action.name,
                            'help': action.help,
                            'type': action.type,
                            'views': [[form_view_id, 'form']],
                            'target': action.target,
                            'domain': action.domain,
                            'context': {'default_err_msg': err_msg},
                            'res_model': action.res_model,
                            'target': 'new'
                        }

            res = super(SaleOrderExtend,self).action_confirm()
            return res


    def reset_to_draft(self):
        self.state = 'draft'

    #credit = fields.Monetary(string='Total Receivable',related='partner_id.credit', store=True)
    not_due_amount_receivable = fields.Monetary(string='Not Due',related='partner_id.not_due_amount_receivable',store=True)
    due_amount_receivable = fields.Monetary(string='Due', related='partner_id.due_amount_receivable',store=True)
    credit_limit = fields.Monetary(string='Credit Limit', related='partner_id.credit_limit',  tracking=True, store=True)
    allowed_credit = fields.Float(string='Remaining Credit Allowed', related='partner_id.allowed_credit',store=True)
    is_credit_limit_bypass = fields.Boolean(string='Is By Pass Credit limit',default=False,copy=False)
    bypass_msg = fields.Text('Credit Limit By Pass Message')
    bypass_msg_disapproved = fields.Text('Credit Limit Dis-approved reason')
    credit_limit_bypass_requested_by_id = fields.Many2one('res.users',string='Credit Limit by Pass Requested By')
    credit_limit_bypass_confirmed_by_id = fields.Many2one('res.users', string='Credit Limit by Pass Confirmed By')
    credit_limit_bypass_approved_by_id = fields.Many2one('res.users', string='Credit Limit by Pass Approved By')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('advance', 'Cash Sales'),
        ('credit', 'Credit Sales'),
        ('sale', 'Sale Order'),
        ('credit_limit_by_pass_request', 'Credit Limit By Pass Request'),
        ('credit_limit_by_pass_confirm','Credit Limit By Pass Confirmed'),
        ('credit_limit_by_pass_approve', 'Credit Limit By Pass Approved'),
        ('credit_limit_by_pass_disapprove', 'Credit Limit By Pass DisApproved'),
        ('credit_limit_by_pass_cancel', 'Credit Limit By Pass Cancelled'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')
