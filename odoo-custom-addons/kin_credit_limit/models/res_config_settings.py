# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_activate_credit_limit = fields.Boolean('Activate Credit Limit', config_parameter = 'kin_credit_limit.is_activate_credit_limit')





