# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

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

    def button_rejected(self):
        model_data_obj = self.env['ir.model.data']
        action = self.env['ir.model.data'].xmlid_to_object('kin_purchase_request.action_reject_purchase_request')
        form_view_id = model_data_obj.xmlid_to_res_id('kin_purchase_request.confirm_purchase_request_reject_view')

        return {
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'res_model': 'purchase.request.reject.wizard',
            'target': 'new'
        }

    def action_reject(self,msg):
        partn_ids = []
        user = self.requested_by
        user_name = user.name
        partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_follower_ids.unlink()
            msg = "Purchase Request (%s) has been rejected by %s, with comment: %s" % (self.name, self.env.user.name,msg)
            subject = 'Purchase Request (%s) has been rejected by %s' % (self.name, self.env.user.name)
            self.message_post(
                body=msg,
                subject=subject, partner_ids=partn_ids,
                subtype_xmlid='mail.mt_comment', force_send=False)
        return super(PurchaseRequest, self).button_rejected()


    def button_approved(self):
        # send email to group
        group_name = 'kin_purchase_request.group_receive_approved_purchase_request_email'
        msg = "Purchase Request (%s) has been approved by (%s)" % (self.name, self.env.user.name)
        subject = 'Purchase Request (%s) has been approved by (%s)' % (self.name, self.env.user.name),
        self.send_email(group_name, subject, msg)
        return super(PurchaseRequest, self).button_approved()


    def button_to_approve(self):
        #send email to approver
        partn_ids = []
        user = self.assigned_to
        user_name = user.name
        partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_follower_ids.unlink()
            msg = "Purchase Request (%s) from %s requires approval from you" % (self.name,self.env.user.name)
            subject = '%s created a Purchase Request (%s) which requires approval from you (%s)' % (self.env.user.name,self.name,user_name)
            self.message_post(
                body=msg,
                subject=subject, partner_ids=partn_ids,
                subtype_xmlid='mail.mt_comment', force_send=False)
        return super(PurchaseRequest, self).button_to_approve()




