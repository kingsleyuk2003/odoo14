# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    expected_finished_date_interval = fields.Integer("Expected Finished Date Interval", config_parameter='kin_helpdesk.expected_finished_date_interval')
