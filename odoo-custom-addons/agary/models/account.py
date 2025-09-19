# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2024  Kinsolve Solutions
# Copyright 2024 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons.base.models.res_currency import Currency




class AccountMove(models.Model):
    _inherit = "account.move"


    @api.model
    def create(self, vals):
        ctx = self.env.context
        branch_id = ctx.get('branch_id')
        if branch_id:
            vals.update({'branch_id': branch_id.id})
        res = super(AccountMove, self).create(vals)
        if not res.branch_id:
            raise UserError('Please select a branch location for the account move create')
        return res

    def write(self, vals):
        for rec in self:
            ctx = self.env.context
            branch_id = ctx.get('branch_id')
            if branch_id :
                vals.update({'branch_id': branch_id.id})
            res = super(AccountMove, rec).write(vals)
            if not branch_id and not rec.branch_id:
                raise UserError('Please select a branch location for the account move update')
            return res

    @api.model
    def amount_to_text(self, amt):
        amount_text = Currency.amount_to_text(amount=amt)
        return amount_text

    def populate_ref_invoice_line_details(self):
        for move in self:
            if not move.is_sale_document(include_receipts=True) or not move.company_id.anglo_saxon_accounting:
                continue
            txt = ''
            for line in move.invoice_line_ids:
                txt += " %s %s(%s) %s | " % (line.name, line.quantity,line.product_uom_id.name,line.price_unit)
            move.ref = txt

        return  super(AccountMove, self)._stock_account_prepare_anglo_saxon_out_lines_vals()


    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        self.populate_ref_invoice_line_details()
        return  super(AccountMove, self)._stock_account_prepare_anglo_saxon_out_lines_vals()

    # delivery_note = fields.Char(string='Delivery Note')
    supplier_ref = fields.Char(string='Suppliers Reference')
    other_ref = fields.Char(string='Other Reference')
    buyer_order_no = fields.Char(string='Buyer Order Number')
    buyer_order_no_dated = fields.Date('Buyer Order Dated')
    dispatch_doc_no = fields.Char('Dispatch Document Number')
    dispatch_doc_no_dated = fields.Date('Dispatch Doc. No. Dated')
    dispatched_through = fields.Char(string='Dispatched Through')
    destination = fields.Char(string='Destination')
    terms_of_delivery = fields.Text(string='Terms of Delivery')

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _calculate_margin_markup_profit(self):
        self.ensure_one()
        if self.cos and (self.price_subtotal > 0) and self.move_id.move_type == "out_invoice":  # Invoice
            total_cos = self.cos * self.quantity
            gross_profit = self.price_subtotal - total_cos
            self.markup = (gross_profit / total_cos) * 100
            self.gross_margin = (gross_profit / self.price_subtotal) * 100
            self.gross_profit = gross_profit
            self.cos_total = total_cos
            self.is_cos = True
            self.has_commission = True
        elif self.cos and (self.price_subtotal < 0) or self.move_id.move_type == "out_refund":  # Refund  Invoice or a negative invoice line
            total_cos = self.cos * self.quantity
            gross_profit = -(self.price_subtotal - total_cos)
            self.markup = (gross_profit / total_cos) * 100
            self.gross_margin = (gross_profit / self.price_subtotal) * 100
            self.gross_profit = gross_profit
            self.cos_total = -total_cos
            self.is_cos = True
            self.has_commission = True

    has_commission = fields.Boolean(string='Has Commission')


class AccountJournal(models.Model):
    _inherit = "account.journal"

    branch_id = fields.Many2one('res.branch', string="Branch")