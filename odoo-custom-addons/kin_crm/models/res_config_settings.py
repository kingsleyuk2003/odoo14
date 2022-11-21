# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_create_quote_on_won = fields.Boolean(string='Create Quotation on Opportunity Won', config_parameter='kin_crm.is_create_quote_on_won')
