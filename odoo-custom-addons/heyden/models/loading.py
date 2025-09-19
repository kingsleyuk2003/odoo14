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


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.depends('quantity')
    def _compute_average_cost(self):
        for quant in self:
            quant.average_cost = quant.value / quant.quantity

    average_cost = fields.Monetary('Average Cost',compute='_compute_average_cost')



class StockPickingHeyden(models.Model):
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
        res = super(StockPickingHeyden, self).button_validate()
        picking_type_code = self.picking_type_code
        purchase_order = self.purchase_id
        if picking_type_code == "incoming" and purchase_order:
            if not self.aftershore_receipt_documents and self.env.company.id == 1 :
                raise UserError('Kindly upload the aftershore receipt documents')

        if self.env.company.id != 1:
            inv = self.create_sales_invoice()
            emp_id = False
            sale_order = self.sale_id
            if sale_order and inv:
                inv.invoice_date = sale_order.date_order
                inv.name = ''
                inv.date = sale_order.date_order
                emp_id = sale_order.emp_hey_id
            if inv :
                inv.emp_hey_id = emp_id or False
                inv.request_validation()
            bill = self.create_purchase_bill()
            if bill :
                inv.emp_hey_id = emp_id or False
                bill.request_validation()

        return res

    aftershore_receipt_documents = fields.Binary(string='After Shore Receipt Documents')
    emp_hey_id = fields.Many2one('employee.heyden', string='Employee Responsible', tracking=True)




class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    @api.onchange('department_id')
    def _onchange_conv_rate(self):
        self.assigned_to = self.sudo().department_id.manager_id.user_id

    department_id = fields.Many2one('hr.department', string='Department')
    emp_hey_id = fields.Many2one('employee.heyden', string='Employee Responsible', tracking=True)
    attachment = fields.Binary(string='Document Attachment')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')
        journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        partner_invoice_id = self.partner_id.address_get(['invoice'])['invoice']
        invoice_vals = {
            'ref': self.partner_ref or '',
            'move_type': move_type,
            'narration': self.notes,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'partner_id': partner_invoice_id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
            'payment_reference': self.partner_ref or '',
            'partner_bank_id': self.partner_id.bank_ids[:1].id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
            'invoice_date' : self.date_order,


        }
        return invoice_vals

    def btn_request_approval(self):
        if self.state == 'done':
            raise UserError('Sorry, the record has already been approved')
        if self.state == 'cancel':
            raise UserError('Sorry, the record is cancelled')

        if self.is_purchase :
            msg = 'Purchase Order with id (%s) requires your approval' % self.name
            self.send_grp_email(grp_name='kin_purchase.group_purchase_order_receive_request_approval_email', subject=msg,msg=msg)
        else:
            msg = 'Procurement Order with id (%s) requires your approval' % self.name
            self.send_grp_email(grp_name='heyden.group_purchase_order_receive_request_approval_email_procurement', subject=msg,msg=msg)


        self.is_request_approval_sent = True
        self.is_request_approval_by = self.env.user
        self.is_request_approval_date = fields.Datetime.now()

    emp_hey_id = fields.Many2one('employee.heyden', string='Employee Responsible', tracking=True)


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
    is_commercial = fields.Boolean(string="Is Commercial Customer")



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_confirmation_values(self):
        return {
            'state': 'sale',
            'date_order': self.date_order,
        }


    def create_advance_invoice_depot(self):
        is_post_invoice_before_delivery = self.env['ir.config_parameter'].sudo().get_param(
            'is_post_invoice_before_delivery', default=False)

        # create advance invoice for depot
        inv = self._create_advance_invoice_depot(final=True)
        inv.sale_order_id = self
        inv.is_advance_invoice = True
        self.is_has_advance_invoice = True
        self.advance_invoice_id = inv
        self.state = 'atl_awaiting_approval'
        emp_id = self.emp_hey_id
        inv.emp_hey_id = emp_id or False
        if is_post_invoice_before_delivery:
            inv.action_post()
            #inv.request_validation()
            #inv.validate_tier() # no effect here. so we depend on the scheduler autovalidate
        return inv

    def action_confirm(self):
        ctx = dict(self._context)
        if self.location_id:
            ctx['atl_depot_id'] = self.location_id.id
        res = super(SaleOrder, self.with_context(ctx)).action_confirm()


        #for commercial customer
        if self.env.company.id != 1 and self.partner_id.is_commercial:
            is_mgt_prod_added = False
            for line in self.order_line:
                # management product already added, so dont repeat it
                if line.product_id.property_account_income_id and line.product_id.property_account_income_id.id == 3642:
                    is_mgt_prod_added = True
            if not is_mgt_prod_added :
                for line in self.order_line:
                    mgt_prod = line.product_id.mgt_product_id
                    inv_line_mgt = {
                        'product_id': mgt_prod.id,
                        'product_uom_qty': line.product_uom_qty,
                        'price_unit': 5,
                        'order_id' : self.id
                    }
                    self.order_line.create(inv_line_mgt)

        for picking in self.picking_ids :
            picking.with_context(atl_depot_id=11).action_assign()
            picking.button_validate()
        return res

    def action_submit_to_manager(self):
        if self.is_other_sale :
            raise UserError('Kindly go through the Retail Sales Order Menu for this operation')
        res = super(SaleOrder, self).action_submit_to_manager()
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

    emp_hey_id = fields.Many2one('employee.heyden', string='Employee Responsible', tracking=True)
    location_id = fields.Many2one('stock.location', string='Stock Location')



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
    emp_hey_id = fields.Many2one('employee.heyden', string='Employee Responsible', tracking=True)

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    emp_hey_id = fields.Many2one('employee.heyden', string='Employee Responsible', tracking=True)


class ProductProductLoading(models.Model):
    _inherit = 'product.template'

    mgt_product_id = fields.Many2one('product.product',string='Management Service')

class DRPInfo(models.Model):
    _inherit = 'dpr.info'
    _rec_name = 'dpr_no'