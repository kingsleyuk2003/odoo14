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
            if not self.aftershore_receipt_documents and self.env.company.id == 1 :
                raise UserError('Kindly upload the aftershore receipt documents')

        if self.env.company.id != 1:
            self.create_sales_invoice()
            self.create_purchase_bill()

        return res

    aftershore_receipt_documents = fields.Binary(string='After Shore Receipt Documents')




class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    @api.onchange('department_id')
    def _onchange_conv_rate(self):
        self.assigned_to = self.sudo().department_id.manager_id.user_id

    department_id = fields.Many2one('hr.department', string='Department')
    employee_id = fields.Many2one('hr.employee', string='Employee Responsible')
    attachment = fields.Binary(string='Document Attachment')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self,vals):
        res = super(PurchaseOrder, self).create(vals)
        return res

    employee_id = fields.Many2one('hr.employee', string='Employee Responsible')


# Copyright 2018-2019 ForgeFlow, S.L.
# ../odoo-custom-addons/purchase_request/wizard/purchase_request_line_make_purchase_order.py
class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    @api.model
    def _prepare_purchase_order(self, picking_type, group_id, company, origin):
        res = super(PurchaseRequestLineMakePurchaseOrder, self)._prepare_purchase_order(picking_type, group_id, company, origin)
        pr_id = self.env.context.get('active_id',False)
        pr_obj = self.env['purchase.request'].browse(pr_id)
        res.update({'employee_id': pr_obj.employee_id.id})
        return res


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self,vals):
        name = vals.get('name', False)
        dup = self.search([('name','=',name)])
        if dup :
            raise UserError('Sorry, %s already exist' % (name))
        res = super(ResPartner, self).create(vals)
        return res


    manager = fields.Char(string='Manager')



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
     res = super(SaleOrder, self).action_confirm()
     for picking in self.picking_ids :
         picking.action_assign()
         picking.button_validate()
     return res

    def _default_get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in self.order_line:
            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is invoiceable
                pending_section = line
                continue
            if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
                continue
            if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                if line.is_downpayment:
                    # Keep down payment lines separately, to put them together
                    # at the end of the invoice, in a specific dedicated section.
                    down_payment_line_ids.append(line.id)
                    continue
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                invoiceable_line_ids.append(line.id)

        return self.env['sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)

    def _get_invoiceable_lines(self, final=False):
        if self.env.company.id != 1:
            return self._default_get_invoiceable_lines(final)

        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self.order_line:
            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is invoiceable
                pending_section = line
                continue
            if (line.qty_to_invoice == 0 and final) or line.display_type == 'line_note':
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                invoiceable_line_ids.append(line.id)
        return self.env['sale.order.line'].browse(invoiceable_line_ids)

    employee_id = fields.Many2one('hr.employee', string='Employee Responsible')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

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

        if self.env.company.id != 1:
            return self._default_prepare_invoice_line(**optional_values)

        self.ensure_one()
        deferred_revenue = self.product_id.account_unearned_revenue_id.id
        if not deferred_revenue:
            raise UserError(_('Please contact the Administrator to set the Unearned revenue account for %s', self.product_id.name))

        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            #'product_id' : self.product_id.product_deferred_revenue_id.id,
            'account_id':deferred_revenue,
           #'product_uom_id': self.product_uom.id,
            'quantity': self.product_uom_qty,
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


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, copy=False,
                               states={'draft': [('readonly', False)]}, default=lambda self: fields.Datetime.now())
    employee_id = fields.Many2one('hr.employee', string='Employee Responsible')

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    employee_id = fields.Many2one('hr.employee', string='Employee Responsible')

class AccountPayment(models.Model):
    _inherit = 'stock.picking'

    employee_id = fields.Many2one('hr.employee', string='Employee Responsible')