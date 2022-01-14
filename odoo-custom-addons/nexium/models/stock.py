# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017 - 2021  Kinsolve Solutions
# Copyright 2017 - 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, float_round, DEFAULT_SERVER_DATETIME_FORMAT
import time
from datetime import datetime
from psycopg2 import OperationalError
import odoo
from datetime import *
from odoo import SUPERUSER_ID


class StockPicking(models.Model):
    _inherit = "stock.picking"
    _order = 'name desc'

    @api.model
    def create(self, vals):
        sale_no = vals.get('origin', False)
        if sale_no:
            sale_order = self.env['sale.order'].search([('name','=',sale_no)])
            if sale_order:
                customer_type = sale_order.customer_type
                if customer_type == 'distributor':
                    vals['picking_type_id'] = 5
        return super(StockPicking, self).create(vals)

    @api.onchange('location_id')
    def change_location_id(self):
        res = {}
        status = self.state
        if status in ['assigned', 'partially_available']:
            res['warning'] = {'title': "Error",
                              'message': 'Please click the "Discard" Button, then click "Unreserve" Button, Make the location changes and click "Reserve" button to change the delivery source location', }

        pack_operation_product_ids = self.move_line_ids_without_package
        for pack_operation_prod in pack_operation_product_ids:
            pack_operation_prod.location_id = self.location_id

    @api.onchange('location_dest_id')
    def change_location_dest_id(self):
        pack_operation_product_ids = self.move_line_ids_without_package
        for pack_operation_prod in pack_operation_product_ids:
            pack_operation_prod.location_dest_id = self.location_dest_id

    def _prepare_refund_bill(self):
        self.ensure_one()
        partner_id = self.env['res.partner'].search([('is_lra', '=', True)])
        if not partner_id:
            raise UserError('Kindly indicate a partner as LRA')
        move_type = self._context.get('default_move_type', 'in_refund')
        journal = self.env['account.move'].with_context(
            default_move_type='in_refund')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting refund purchase journal for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))

        partner_invoice_id = partner_id.address_get(['invoice'])['invoice']
        invoice_vals = {
            'ref': self.name or '',
            'move_type': move_type,
            'narration': self.note,
            'currency_id': self.company_id.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'partner_id': partner_id.id,
            # 'fiscal_position_id': (
            #         self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
            'payment_reference': self.origin or '',
            'invoice_origin': self.name,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals

    def _prepare_account_move_line_refund(self, product_id=False, move=False, charge_id=False, qty_to_invoice=False):
        self.ensure_one()
        if self.sale_id:
            if charge_id.charges_percentage == 0:
                raise UserError(
                    'Please set a percentage cost of %s for %s ' % (charge_id.product_charges_id.name, product_id.name))
            # price_unit = self.sale_id.order_line.filtered(lambda line: line.product_id.is_petroleum_product == True).mapped('price_unit')[0]

            res = {
                'display_type': False,
                'sequence': 10,
                'name': '%s percent %s of %s%s  %s with reference : %s: %s' % (
                    charge_id.charges_percentage, charge_id.product_charges_id.name, qty_to_invoice, charge_id.product_charges_id.uom_po_id.name, product_id.name, self.name,
                    self.origin),
                'product_id': charge_id.product_charges_id.id,
                'product_uom_id': charge_id.product_charges_id.uom_po_id.id,
                'quantity': (qty_to_invoice * (charge_id.charges_percentage / 100)),
                'price_unit': 1,
                # 'tax_ids': [(6, 0, self.taxes_id.ids)],
                # 'analytic_account_id': self.account_analytic_id.id,
                # 'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
                # 'purchase_line_id': self.id,
            }
            if not move:
                return res

            if self.currency_id == move.company_id.currency_id:
                currency = False
            else:
                currency = move.currency_id

            res.update({
                'move_id': move.id,
                'currency_id': currency and currency.id or False,
                'date_maturity': move.invoice_date_due,
                'partner_id': move.partner_id.id,
            })
            return res

    def action_create_refund_bill(self):
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')

        # 1) Prepare invoice vals
        invoice_vals_list = []
        invoice_vals = self._prepare_refund_bill()
        qty_to_invoice = 0
        qty_to_invoice += sum(self.move_ids_without_package.mapped('quantity_done'))
        if not float_is_zero(qty_to_invoice, precision_digits=precision):
            for line in self.move_ids_without_package:
                qty_to_invoice = line.quantity_done
                charges_products = line.product_id.charges_ids
                for charge_id in charges_products:
                    invoice_vals['invoice_line_ids'].append(
                        (0, 0, self._prepare_account_move_line_refund(product_id=line.product_id, charge_id=charge_id, qty_to_invoice=qty_to_invoice)))
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(
                _('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(
            default_move_type='in_refund')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)
            bill_id = moves.id
            bill_move = self.env['account.move'].browse(bill_id)
            bill_move.invoice_date = fields.Datetime.now()
            bill_move.picking_do_id = self
            moves.action_post()
            bill_move.is_charge_bill = True
            bill_move.is_from_inventory = True

            # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        #moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()
        return moves

    def _prepare_bill(self):
        self.ensure_one()
        partner_id = self.env['res.partner'].search([('is_lra', '=', True)])
        if not partner_id:
            raise UserError('Kindly indicate a partner as LRA')
        move_type = self._context.get('default_move_type', 'in_invoice')
        journal = self.env['account.move'].with_context(
            default_move_type=move_type)._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))

        partner_invoice_id = partner_id.address_get(['invoice'])['invoice']

        invoice_vals = {
            'ref': self.name or '',
            'move_type': move_type,
            'narration': self.note,
            'currency_id': self.company_id.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'partner_id': partner_id.id,
            # 'fiscal_position_id': (
            #         self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
            'payment_reference': self.origin or '',
            'invoice_origin': self.origin,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals

    def _prepare_account_move_line(self, product_id=False, move=False, charge_id=False, qty_to_invoice=False):
        self.ensure_one()
        if self.sale_id:
            if charge_id.charges_percentage == 0:
                raise UserError(
                    'Please set a percentage cost of %s for %s ' % (charge_id.product_charges_id.name, product_id.name))
            # price_unit = self.sale_id.order_line.filtered(lambda line: line.product_id.is_petroleum_product == True).mapped('price_unit')[0]

            res = {
                'display_type': False,
                'sequence': 10,
                'name': '%s percent %s of %s%s  %s with reference : %s: %s' % (
                    charge_id.charges_percentage, charge_id.product_charges_id.name, qty_to_invoice, charge_id.product_charges_id.uom_po_id.name, product_id.name, self.name,
                    self.origin),
                'product_id': charge_id.product_charges_id.id,
                'product_uom_id': charge_id.product_charges_id.uom_po_id.id,
                'quantity': (qty_to_invoice * (charge_id.charges_percentage / 100)),
                'price_unit': 1,
                # 'tax_ids': [(6, 0, self.taxes_id.ids)],
                # 'analytic_account_id': self.account_analytic_id.id,
                # 'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
                # 'purchase_line_id': self.id,
            }
            if not move:
                return res

            if self.currency_id == move.company_id.currency_id:
                currency = False
            else:
                currency = move.currency_id

            res.update({
                'move_id': move.id,
                'currency_id': currency and currency.id or False,
                'date_maturity': move.invoice_date_due,
                'partner_id': move.partner_id.id,
            })
            return res

    # reate LRA bill
    def action_create_bill(self, sale_order):
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')

        # 1) Prepare invoice vals
        invoice_vals_list = []
        invoice_vals = self._prepare_bill()
        qty_to_invoice = 0
        qty_to_invoice += sum(self.move_ids_without_package.mapped('quantity_done'))
        if not float_is_zero(qty_to_invoice, precision_digits=precision):
            for line in self.move_ids_without_package:
                qty_to_invoice = line.quantity_done
                charges_products = line.product_id.charges_ids
                for charge_id in charges_products:
                    invoice_vals['invoice_line_ids'].append((0, 0, self._prepare_account_move_line(
                        product_id=line.product_id, charge_id=charge_id, qty_to_invoice=qty_to_invoice)))
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(
                _('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(
            default_move_type='in_invoice')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)
            bill_id = moves.id
            bill_move = self.env['account.move'].browse(bill_id)
            bill_move.invoice_date = fields.Datetime.now()
            bill_move.picking_do_id = self
            moves.action_post()
            bill_move.sale_ids = sale_order
            bill_move.is_charge_bill = True
            bill_move.is_from_inventory = True

            # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(lambda m: m.currency_id.round(m.amount_total)
                       < 0).action_switch_invoice_into_refund_credit_note()
        return moves

    def button_validate(self):
        res = super(StockPicking, self).button_validate()

        if res != True and res.get('name') == 'Immediate Transfer?':
            return res
        if res != True and res.get('name') == 'Create Backorder?':
            return res

        if self.is_release_order and not self.release_order_upload:
            raise UserError('Kindly attach the signed release order')

        if self.is_tank_to_tank and not self.tank_to_tank_upload:
            raise UserError('Kindly attach the signed tank to tank document')

        if self.invoice_id :
            self.env.cr.execute("UPDATE account_move SET picking_do_id = %s , do_number = %s , po_number = %s WHERE id = %s", (self.id, self.name, self.po_number, self.invoice_id.id))

        sale_order = self.sale_id
        if sale_order and self.picking_type_code == 'outgoing' and not self.is_duty_free:
            # create charges bill for vendor LRA
            self.bill_id = self.action_create_bill(sale_order)

        if sale_order and self.picking_type_code == 'incoming' and not self.is_duty_free:
            # create a refurn bill for the vendor LRA
            self.bill_id = self.action_create_refund_bill()
        return res

    @api.model
    def get_release_tank_attr(self):
        attn = self.env['ir.config_parameter'].sudo(
        ).get_param('attn', default=False),
        role = self.env['ir.config_parameter'].sudo(
        ).get_param('role', default=False),
        to_address = self.env['ir.config_parameter'].sudo(
        ).get_param('to_address', default=False),
        attn_tank = self.env['ir.config_parameter'].sudo(
        ).get_param('attn_tank', default=False),
        role_tank = self.env['ir.config_parameter'].sudo(
        ).get_param('role_tank', default=False),
        to_address_tank = self.env['ir.config_parameter'].sudo(
        ).get_param('to_address_tank', default=False)

    @api.depends('move_ids_without_package.quantity_done')
    def _compute_amount_in_words(self):
        for rec in self:
            current_curr = self.env.company.currency_id
            if current_curr:
                if self.move_ids_without_package:
                    amount_in_words = current_curr.amount_to_text(
                        self.move_ids_without_package[0].quantity_done)
                    rec.amount_in_words = amount_in_words.replace(
                        'Dollars', '').replace('Cents', '') + ' Gallons'
            else:
                rec.amount_in_words = False

    amount_in_words = fields.Char(
        string="Amount in Words", store=True, compute='_compute_amount_in_words')

    is_duty_free = fields.Boolean(string='IS DUTY FREE')
    bill_id = fields.Many2one('account.move', string='LRA Bill')
    po_number = fields.Char(string="PO Number")
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_src_id,
        check_company=True, readonly=True, required=True,
        states={'draft': [('readonly', False)], 'waiting': [('readonly', False)], 'confirmed': [('readonly', False)]})
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_dest_id,
        check_company=True, readonly=True, required=True,
        states={'draft': [('readonly', False)], 'waiting': [('readonly', False)], 'confirmed': [('readonly', False)], 'assigned': [('readonly', False)]})

    is_release_order = fields.Boolean(string="Is Release Order")
    release_order_no = fields.Char(string='Release Order Ref #')
    attn = fields.Char(string="Attn", default=lambda self: self.env['ir.config_parameter'].sudo(
    ).get_param('attn', default=False))
    role = fields.Char(string="Role", default=lambda self: self.env['ir.config_parameter'].sudo(
    ).get_param('role', default=False))
    to_address = fields.Char(string="To Address", default=lambda self: self.env['ir.config_parameter'].sudo(
    ).get_param('to_address', default=False))
    release_order_upload = fields.Binary(string="Release Order Upload")

    is_tank_to_tank = fields.Boolean(string="Is Tank to Tank Transfer")
    attn_tank = fields.Char(string="Attn", default=lambda self: self.env['ir.config_parameter'].sudo(
    ).get_param('attn_tank', default=False))
    role_tank = fields.Char(string="Role", default=lambda self: self.env['ir.config_parameter'].sudo(
    ).get_param('role_tank', default=False))
    to_address_tank = fields.Char(string="To Address", default=lambda self: self.env['ir.config_parameter'].sudo(
    ).get_param('to_address_tank', default=False))
    tank_to_tank_upload = fields.Binary(string="Tank to Tank Upload")
