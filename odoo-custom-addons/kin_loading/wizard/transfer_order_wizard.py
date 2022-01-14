# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import *

class TransferOrderWizard(models.TransientModel):
    _name = 'transfer.order.wizard'

    def action_generate_transfer_order(self):
        order_id = self.env.context['the_order_id']
        sale_order = self.env['sale.order'].browse(order_id)
        #authorization_code = sale_order.authorization_code
        is_has_advance_invoice = sale_order.is_has_advance_invoice

        ctx = {
                #'authorization_code': authorization_code,
                'is_order_transfer_btn': self.env.context['is_order_transfer_btn'],
                'is_has_advance_invoice':is_has_advance_invoice,
                'recipient_id' :self.recipient_id,
                #'location_dest_id':self.recipient_id.property_stock_customer.id,
            }

        res = sale_order.with_context(ctx).action_create_transfer_order()
        # if res:
        #     return sale_order.action_view_transfers()
        # else:
        #     raise UserError(_(
        #         "Sorry, No Requested Ticket Qty. was set for any of the product to be delivered"))


    def _populate_order_lines(self):
        order_id = self.env.context['active_id']
        order_lines = self.env['sale.order.line'].search([('order_id','=',order_id)])
        self.order_line_ids = order_lines

    order_line_ids = fields.Many2many('sale.order.line', string='Order Lines')
    recipient_id = fields.Many2one('res.partner',string='Product Transfer Recipient')


