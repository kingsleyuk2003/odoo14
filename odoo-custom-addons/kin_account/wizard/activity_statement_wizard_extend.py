# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models


class ActivityStatementWizard(models.TransientModel):
    _inherit = 'activity.statement.wizard'

    def send_mass_email_activity_statement(self,partners):
        company_email = self.env.user.company_id.email.strip()
        for partner in partners:
            partner_email = partner.email or False
            if company_email and partner_email:
                mail_template = partner.env.ref('kin_account.mail_template_partner_activity_statement_email')
                mail_template.send_mail(partner.id, force_send=False)
        return

    def action_statement_send(self):
        partner_id = self.env.context.get('active_ids', [])

        if len(partner_id) > 1 :
            partners = self.env['res.partner'].browse(partner_id)
            self.send_mass_email_activity_statement(partners)

        else:
            template_id = self.env['ir.model.data'].xmlid_to_res_id('kin_account.mail_template_partner_activity_statement_email', raise_if_not_found=False)

            ctx = {
                'default_model': 'res.partner',
                'default_res_id': partner_id[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                # 'mark_so_as_sent': True,
                # 'custom_layout': "mail.mail_notification_paynow",
                # 'proforma': self.env.context.get('proforma', False),
                'force_email': True
            }
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
            }
