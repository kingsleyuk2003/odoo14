# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, vals):
        group_obj = self.env.ref('kin_stock.group_allow_invoice_edit_inventory')
        user = self.env.user
        for rec in self:
            if rec.is_from_inventory and user not in group_obj.users:
                raise UserError('Sorry, you cannot edit this invoice')
        res = super(AccountMove, self).write(vals)
        return res


    is_from_inventory = fields.Boolean(string='Is from Inventory',readonly=1)
