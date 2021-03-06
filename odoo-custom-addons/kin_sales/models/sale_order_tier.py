# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019-2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order','tier.validation']
    _state_from = ["draft","sent"]
    _state_to = ['sale']
    _tier_validation_manual_config = False

    @api.model
    def _get_under_validation_exceptions(self):
        res = super(SaleOrder, self)._get_under_validation_exceptions()
        res.append("is_request_approval_sent")
        res.append("is_request_approval_by")
        res.append("is_request_approval_date")
        return res


class TierDefinition(models.Model):
    _inherit = 'tier.definition'

    @api.model
    def _get_tier_validation_model_names(self):
        res = super(TierDefinition, self)._get_tier_validation_model_names()
        res.append('sale.order')
        return res