# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def send_grp_email(self, grp_name, subject, msg):
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref(grp_name)
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)
        if partn_ids:
            # self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partn_ids, subtype_xmlid='mail.mt_comment',
                              force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))


    def send_email(self, grp_name, subject, msg):
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref(grp_name)
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)
        if partn_ids:
            #self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))


    def button_draft(self):
        self.is_request_approval_sent = False
        self.is_request_approval_by = False
        self.is_request_approval_date = False
        return super(PurchaseOrder, self).button_draft()

    def btn_request_approval(self):
        if self.state == 'done':
            raise UserError('Sorry, the record has already been approved')
        if self.state == 'cancel' :
            raise UserError('Sorry, the record is cancelled')
        msg = 'Purchase Order with id (%s) requires your approval' % self.name
        self.send_grp_email(grp_name='kin_purchase.group_purchase_order_receive_request_approval_email', subject=msg, msg=msg)
        self.is_request_approval_sent = True
        self.is_request_approval_by = self.env.user
        self.is_request_approval_date = fields.Datetime.now()

    def button_confirm(self):
        # Receive sales order approved email notification
        msg = 'A New purchase order has been approved  with source document (%s)  for the vendor (%s)' % (
                            self.name, self.partner_id.name)
        self.send_email(grp_name='kin_purchase.group_purchase_order_approved_email',
                        subject=msg,
                        msg=msg)
        return super(PurchaseOrder, self).button_confirm()

    @api.depends('order_line.invoice_lines.move_id')
    def _compute_invoice(self):
        for order in self:
            invoices = order.mapped('order_line.invoice_lines.move_id')
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)


    invoice_ids = fields.Many2many('account.move', 'purchase_account_move', 'purchase_id', 'account_id',  compute="_compute_invoice", string='Bills', copy=False, store=True)
    is_request_approval_sent = fields.Boolean(string='Is Request Approval Sent', copy=False, tracking=True)
    is_request_approval_by = fields.Many2one('res.users', string='Requested By', copy=False, tracking=True)
    is_request_approval_date = fields.Datetime(string='Request Approval Date', copy=False, tracking=True)

