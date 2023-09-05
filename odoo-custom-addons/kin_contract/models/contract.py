# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _

class ContractExtend(models.Model) :
    _inherit = 'contract.contract'

    # Extending from ... / contract / models / contract.py: 594
    def _recurring_create_invoice(self,date_ref = False):
        res = super(ContractExtend, self)._recurring_create_invoice(date_ref)

        if res :
            is_post_recurring_invoice = self.env['ir.config_parameter'].sudo().get_param('kin_contract.is_post_recurring_invoice',default=False)
            is_send_recurring_email = self.env['ir.config_parameter'].sudo().get_param('kin_contract.is_send_recurring_email', default=False)
            email_from = self.env['ir.config_parameter'].sudo().get_param('kin_contract.email_from', default=False)
            email_cc = self.env['ir.config_parameter'].sudo().get_param('kin_contract.email_cc', default=False)

            #confirm and post the invoice
            if is_post_recurring_invoice :
                res.action_post()

            #send email to customer
            if is_send_recurring_email and self.is_autosend_invoice:
                template = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)
                if email_from :
                    template.email_from = email_from
                if email_cc :
                    template.email_cc = email_cc
                template.send_mail(res.id, force_send=False)

        return res

    is_autosend_invoice = fields.Boolean(string="Auto Send Recurring Invoice", default=True)
