# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2022 - 2022  Kinsolve Solutions
# Copyright 2022 - 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
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

class ProductProductLoading(models.Model):
    _inherit = 'product.template'

    conv_rate = fields.Float(string='Conv. Rate')



class StockPicking(models.Model):
    _inherit = "stock.picking"
    _order = 'name desc'

    def btn_print_loading_ticket(self):
        # if self.is_loading_ticket_printed :
        #     raise UserError(_('Sorry, Loading Ticket can only be printed once'))
        self.is_loading_ticket_printed = True
        return self.env.ref('heyden.action_report_loading_ticket_heyden').report_action(self)


    def btn_print_waybill(self):
        # if self.is_waybill_printed:
        #     raise UserError(_('Sorry, Waybill can only be printed once'))
        self.is_waybill_printed = True
        if not self.dispatch_date :
            self.dispatch_date = date.today()
            self.loaded_date = self.dispatch_date
            self.depot_officer_id = self.env.user
        return self.env.ref('heyden.action_report_delivery_heyden').report_action(self)

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        picking_type_code = self.picking_type_code
        purchase_order = self.purchase_id
        if picking_type_code == "incoming" and purchase_order:
            if not self.aftershore_receipt_documents :
                raise UserError('Kindly upload the aftershore receipt documents')

        return res

    aftershore_receipt_documents = fields.Binary(string='After Shore Receipt Documents')

class PurchaseOrderLineExtend(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            line.conv_rate = line.product_id.conv_rate
            line.unit_price_ltr = line.product_id.standard_price

    @api.onchange('conv_rate','product_qty')
    def _onchange_conv_rate(self):
        for line in self:
            line.product_qty_ltr = line.product_qty * line.conv_rate

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                vals['partner'])
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if line.order_id.is_purchase :
                line.update({
                    'price_unit':  (line.product_qty * line.conv_rate) * line.unit_price_ltr
                })



    unit_price_ltr = fields.Float(string='Ltr. Price')
    product_qty_ltr = fields.Float(string='Ltr. Qty')


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def create(self, vals):
        return super(PurchaseOrder, self).create(vals)

    def write(self,vals):
        return super(PurchaseOrder, self).write(vals)