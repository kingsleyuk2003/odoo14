# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    def button_create_landed_costs(self):
        """Create a `stock.landed.cost` record associated to the account move of `self`, each
        `stock.landed.costs` lines mirroring the current `account.move.line` of self.
        """
        self.ensure_one()
        landed_costs_lines = self.line_ids.filtered(lambda line: line.is_landed_costs_line)

        landed_costs = self.env['stock.landed.cost'].create({
            'vendor_bill_id': self.id,
            'cost_lines': [(0, 0, {
                'product_id': l.product_id.id,
                'name': l.product_id.name,
                'account_id':l.product_id.product_tmpl_id.get_product_accounts()['expense'] and l.product_id.product_tmpl_id.get_product_accounts()['expense'].id or l.product_id.product_tmpl_id.get_product_accounts()['stock_input'].id,
                'price_unit': l.currency_id._convert(l.price_subtotal, l.company_currency_id, l.company_id, l.move_id.date),
                'split_method': l.product_id.split_method_landed_cost or 'equal',
            }) for l in landed_costs_lines],
        })
        action = self.env["ir.actions.actions"]._for_xml_id("stock_landed_costs.action_stock_landed_cost")
        return dict(action, view_mode='form', res_id=landed_costs.id, views=[(False, 'form')])


    def write(self, vals):
        group_obj = self.env.ref('kin_stock.group_allow_invoice_edit_inventory')
        user = self.env.user
        for rec in self:
            if rec.is_from_inventory and user not in group_obj.users:
                raise UserError('Sorry, you cannot edit this invoice')
        res = super(AccountMove, self).write(vals)
        return res


    is_from_inventory = fields.Boolean(string='Is from Inventory',readonly=1)
