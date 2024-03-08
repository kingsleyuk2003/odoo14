# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019-2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from odoo import api, fields, models, _

class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order','tier.validation']
    _state_from = ["draft","sent","to approve"]
    _state_to = ["purchase"]
    _tier_validation_manual_config = False


class TierDefinition(models.Model):
    _inherit = 'tier.definition'

    @api.model
    def _get_tier_validation_model_names(self):
        res = super(TierDefinition, self)._get_tier_validation_model_names()
        res.append('purchase.order')
        return res

class TierValidation(models.AbstractModel):
    _inherit = "tier.validation"

    @api.model
    def _get_under_validation_exceptions(self):
        """Extend for more field exceptions."""
        res = super(TierValidation, self)._get_under_validation_exceptions()
        #res.append('order_line')
        res.append('depot_id')
        res.append('emp_hey_id')
        return res


