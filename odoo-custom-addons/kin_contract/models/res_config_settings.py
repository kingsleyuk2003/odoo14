# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     res.update({
    #         'restrict_days': self.env['ir.config_parameter'].sudo().get_param('kin_account.restrict_days', default=0),
    #         'restrict_back_date': self.env['ir.config_parameter'].sudo().get_param('kin_account.restrict_back_date', default=False),
    #     })
    #     return res
    #
    # def set_values(self):
    #     super(ResConfigSettings, self).set_values()
    #     self.env['ir.config_parameter'].sudo().set_param('kin_account.restrict_back_date', self.restrict_back_date)
    #     self.env['ir.config_parameter'].sudo().set_param('kin_account.restrict_days', self.restrict_days)
    #
    # restrict_days = fields.Boolean("Restrict Days Count")
    # restrict_back_date = fields.Boolean('Restrict Back Dating')

    is_post_recurring_invoice = fields.Boolean('Auto-Post Recurring Invoice', default=True, config_parameter='kin_contract.is_post_recurring_invoice')
    is_send_recurring_email = fields.Boolean("Auto-Send Recurring Invoice Email", default=True, config_parameter='kin_contract.is_send_recurring_email')
    email_from = fields.Char(string='Email From',config_parameter='kin_contract.email_from')
    email_cc = fields.Char(string='Email CC',config_parameter='kin_contract.email_cc')





