# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright 2024  Kinsolve Solutions
# Copyright 2024 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from datetime import datetime, timedelta , date


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_confirmation_values(self):
        return {
            'state': 'sale'
        }


    sale_note = fields.Text(string='Sales Person Note')
    account_note = fields.Text(string="Accountant's Note")
    partner_balance = fields.Monetary(related='partner_id.credit', string="Account Balance")




class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    @api.onchange('product_id')
    def product_id_change(self):
        self.has_commission = self.product_id.has_commission

        res = super(SaleOrderLine,self).product_id_change()
        self.name = self.product_id.name
        return res

    def _default_prepare_invoice_line(self, **optional_values):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        :param optional_values: any parameter that should be added to the returned invoice line
        """
        self.ensure_one()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.tax_id.ids)],
            'analytic_account_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'sale_line_ids': [(4, self.id)],
        }
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res


    def _prepare_invoice_line(self, **optional_values):
        invoice_line_vals = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        invoice_line_vals['has_commission'] = self.has_commission
        return invoice_line_vals



    has_commission = fields.Boolean(string='Commission')





