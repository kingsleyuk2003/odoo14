# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright 2024  Kinsolve Solutions
# Copyright 2024 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from datetime import datetime, timedelta , date


class OtherProductCategory(models.Model):
    _name = 'other.prod.category'

    name = fields.Char(string='Name')


class ProductTemplateExtend(models.Model):
    _inherit = 'product.template'

    other_category_id = fields.Many2one('other.prod.category' ,string='Product Category B', track_visibility='always')
    has_commission = fields.Boolean(string='Has Commission')

class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def post_inventory(self):
        ctx = self.env.context.copy()
        ctx.update({"branch_id": self.branch_id})
        res = super(StockInventory,self.with_context(ctx)).post_inventory()
        return res



