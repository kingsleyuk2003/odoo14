# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_send_email_expiry_finish = fields.Boolean(string='Send Email Notification for Expired Tickets',  config_parameter='fibernet.is_send_email_expiry_finish')

