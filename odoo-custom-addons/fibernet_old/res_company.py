# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2020  Kinsolve Solutions
# Copyright 2020 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _


class ResCompanyReport(models.Model):
    _inherit = "res.company"

    header_data_receipt_kkon = fields.Html(string='Receipt Header Data KKON/FOB', help="e.g. Addresses of head Office and Tel No should be added here ")










