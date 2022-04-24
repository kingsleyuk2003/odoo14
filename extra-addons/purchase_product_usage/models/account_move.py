# Copyright 2019 Aleph Objects, Inc.
# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    @api.model_create_multi
    def create(self, vals):
        res = super(AccountMoveLine, self).create(vals)
        for line in res:
            if line.purchase_line_id.usage_id.account_id:
                line.account_id = line.purchase_line_id.usage_id.account_id
        return res


