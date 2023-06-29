# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2023  Kinsolve Solutions
# Copyright 2023 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from datetime import datetime, timedelta
from odoo import api, fields, models, _

class ResPartnerExtend(models.Model):
    _inherit = 'res.partner'


    def btn_confirm(self):
        self.state = 'confirm'
        partn_ids = []
        group_obj = self.env.ref('kin_partner_workflow.group_partner_workflow_manager')
        for user in group_obj.users:
            partn_ids.append(user.partner_id.id)

        self.message_post(body=_('New Partner (%s) has been Created by %s, and requires approval to be active') % (
            self.name, self.env.user.name),
                          subject='A New Partner has been created',partner_ids=partn_ids, subtype_xmlid='mail.mt_comment', force_send=False)


    def btn_activate(self):
        self.state = 'active'
        self.active = True


    def action_disapprove(self,msg):
        self.state = 'draft'
        # Notify the Initiator
        user_id = self.init_user_id

        if user_id.email:
            partn_ids = []
            partn_ids.append(user_id.partner_id.id)
            self.message_post(body=_('Sorry, The new partner record - (%s), created by you has been dis-approved by %s. Reason - %s') % (self.name, self.env.user.name, msg),subject='Dis-approved new customer',partner_ids=partn_ids, subtype_xmlid='mail.mt_comment', force_send=False)
        return self.write({'state': 'draft', 'disapprove_id': self.env.user.id,
                           'disapprove_date': datetime.today(), 'reason_disapprove': msg})


    def btn_deactivate(self):
        self.state = 'not_active'
        self.active = False


    def btn_reset(self):
        self.state = 'draft'

    @api.model
    def create(self, vals):
        res = super(ResPartnerExtend,self).create(vals)
        if res.customer_rank or res.supplier_rank:
            res.active = False
            res.state = 'draft'
        else:
            res.state = 'active'
        return res



    name = fields.Char('Name')
    init_user_id = fields.Many2one('res.users', string='User Initiator',default=lambda self: self.env.user, readonly=True)
    state = fields.Selection(
        [ ('draft', 'Draft'),
          ('confirm', 'Confirm'),
            ('active', 'Approved and Active'),
         ('not_active', 'Not Active')],
        default='draft', track_visibility='onchange')
    reason_disapprove = fields.Text(string='Reason for Dis-Approval')
    disapprove_id = fields.Many2one('res.users', string='Disapproved By', ondelete='restrict')
    disapprove_date = fields.Datetime(string='Disapproved Date')

