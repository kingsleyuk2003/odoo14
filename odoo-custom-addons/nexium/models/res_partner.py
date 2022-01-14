# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017 - 2021  Kinsolve Solutions
# Copyright 2017 - 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _



class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_lra = fields.Boolean(string='is LRA')
    contact_name = fields.Char(string='Contact Name')