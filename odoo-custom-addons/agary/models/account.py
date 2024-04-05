# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2024  Kinsolve Solutions
# Copyright 2024 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        ctx = self.env.context
        branch_id = ctx.get('branch_id')
        if not branch_id and not res.branch_id:
            raise UserError('Please select a branch location for the account move create')
        return res

    def write(self, vals):
        for rec in self:
            res = super(AccountMove, rec).write(vals)
            ctx = self.env.context
            branch_id = ctx.get('branch_id')
            if not branch_id and not rec.branch_id:
                raise UserError('Please select a branch location for the account move update')
            return res

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    has_commission = fields.Boolean(string='Has Commission')

