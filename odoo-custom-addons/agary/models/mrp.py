# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2024  Kinsolve Solutions
# Copyright 2024 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def button_mark_done(self):
        ctx = self.env.context.copy()
        ctx.update({"branch_id": self.branch_id})
        res = super(MrpProduction, self.with_context(ctx)).button_mark_done()
        return res

    branch_id = fields.Many2one('res.branch', string='Branch', default=lambda self: self.env.user.branch_id)