# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017 - 2021  Kinsolve Solutions
# Copyright 2017 - 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare

class StockMove(models.Model):
    _inherit = "stock.move"

    def write(self,vals):
        res = super(StockMove, self).write(vals)
        picking_id = vals.get('picking_id',False)
        if picking_id:
            # see: ../addons/stock/stock.py:821
            # Change locations of moves if those of the picking change
            picking_obj = self.env['stock.picking'].browse(picking_id)
            location_id = picking_obj.location_id
            location_dest_id = picking_obj.location_dest_id
            picking_obj.write({'location_id':location_id.id,'location_dest_id': location_dest_id.id})
        return res


class StockPicking(models.Model):
    _inherit = "stock.picking"
    _order = 'name desc'

    def send_grp_email(self, grp_name, subject, msg):
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref(grp_name)
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)
        if partn_ids:
            # self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partn_ids, subtype_xmlid='mail.mt_comment',
                              force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))


    def btn_request_approval(self):
        if self.state == 'done':
            raise UserError('Sorry, the record has already been approved')
        if self.state == 'cancel':
            raise UserError('Sorry, the record is cancelled')
        msg = 'Stock Transfer (%s) from %s requires your approval' % (self.name, self.env.user.name)
        self.send_grp_email(grp_name='kin_stock.group_stock_picking_receive_request_approval_email', subject=msg, msg=msg)
        self.is_request_approval_sent = True
        self.is_request_approval_by = self.env.user
        self.is_request_approval_date = fields.Datetime.now()

    is_request_approval_sent = fields.Boolean(string='Is Request Approval Sent', copy=False, tracking=True)
    is_request_approval_by = fields.Many2one('res.users', string='Requested By', copy=False, tracking=True)
    is_request_approval_date = fields.Datetime(string='Request Approval Date', copy=False, tracking=True)

    def write(self, vals):
        location_id = vals.get('location_id', False)
        location_dest_id = vals.get('location_dest_id', False)

        if location_id :
            for move_line in self.move_line_ids:
                move_line.location_id = location_id

        if location_dest_id:
            for move_line in self.move_line_ids:
                move_line.location_dest_id = location_dest_id

        res = super(StockPicking, self).write(vals)
        return res



    def _check_qty_demand_done(self, quantity_demanded, quantity_done):
        allow_over_transfer = self.env['ir.config_parameter'].sudo().get_param('allow_over_transfer', default=False)
        if quantity_done > quantity_demanded and not allow_over_transfer:
            raise UserError(
                'Quantity done (%s) is higher than Quantity Demanded (%s)' % (quantity_done, quantity_demanded))

    def button_validate(self):
        # this fixes the mov lines not getting update when the source/destination is changed on the stock pikcing and validated without clicking save button
        # for move_line in self.move_line_ids:
        #     move_line.location_id = self.location_id
        #     move_line.location_dest_id = self.location_dest_id

        #check if the quantity done is more than the qty demanded
        for move in self.move_ids_without_package : # dont use move_line_ids. it fails for internal transfer
            quantity_done = round(move.quantity_done,2)
            quantity_demanded = round(move.product_uom_qty,2)

            self._check_qty_demand_done(quantity_demanded, quantity_done)

        res = super(StockPicking, self).button_validate()
        if res != True and res.get('name') == 'Immediate Transfer?':
            return res
        if res != True and res.get('name') == 'Create Backorder?':
            return res

        self.create_purchase_bill()
        inv = self.with_context(picking_name=self.name).create_sales_invoice()
        if self.picking_type_code == 'incoming' and self.so_count:
            inv.action_switch_invoice_into_refund_credit_note()
        return res


    def create_purchase_bill(self):
        # create purchase bill
        purchase_order = self.purchase_id
        create_vendor_bill = self.env['ir.config_parameter'].sudo().get_param('create_vendor_bill', default=False)
        post_vendor_bill = self.env['ir.config_parameter'].sudo().get_param('post_vendor_bill', default=False)
        if purchase_order and create_vendor_bill:
            dict = purchase_order.action_create_invoice()
            bill_id = dict['res_id']
            bill_move = self.env['account.move'].browse(bill_id)
            bill_move.invoice_date = fields.Datetime.now()
            if post_vendor_bill:
                bill_move.action_post()
            bill_move.is_from_inventory = True
            self.invoice_id = bill_move
            return bill_move
        return False

    def create_sales_invoice(self):
        # create sales invoice
        sale_order = self.sale_id
        create_customer_invoice = self.env['ir.config_parameter'].sudo().get_param('create_customer_invoice',
                                                                                   default=False)
        post_customer_invoice = self.env['ir.config_parameter'].sudo().get_param('post_customer_invoice', default=False)
        if sale_order and create_customer_invoice:
            inv = sale_order._create_invoices(final=True)
            inv.sale_ids = sale_order
            if post_customer_invoice:
                inv.action_post()
            inv.is_from_inventory = True
            self.invoice_id = inv
            return inv
        return False

    # def _prepare_refund_invoice(self):
    #     self.ensure_one()
    #     journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
    #     if not journal:
    #         raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))
    #     sale_order = self.sale_id
    #     invoice_vals = {
    #         'ref': sale_order.client_order_ref or '',
    #         'move_type': 'in_invoice',
    #         'narration': sale_order.note,
    #         'currency_id': sale_order.pricelist_id.currency_id.id,
    #         'campaign_id': sale_order.campaign_id.id,
    #         'medium_id': sale_order.medium_id.id,
    #         'source_id': sale_order.source_id.id,
    #         'invoice_user_id': sale_order.user_id and sale_order.user_id.id,
    #         'team_id': sale_order.team_id.id,
    #         'partner_id': sale_order.partner_invoice_id.id,
    #         'partner_shipping_id': sale_order.partner_shipping_id.id,
    #         'fiscal_position_id': (sale_order.fiscal_position_id or sale_order.fiscal_position_id.get_fiscal_position(sale_order.partner_invoice_id.id)).id,
    #         'partner_bank_id': sale_order.company_id.partner_id.bank_ids[:1].id,
    #         'journal_id': journal.id,  # company comes from the journal
    #         'invoice_origin': sale_order.name,
    #         'invoice_payment_term_id': sale_order.payment_term_id.id,
    #         'payment_reference': sale_order.reference,
    #         'transaction_ids': [(6, 0, sale_order.transaction_ids.ids)],
    #         'invoice_line_ids': [],
    #         'company_id': sale_order.company_id.id,
    #     }
    #     return invoice_vals

    # def _get_invoiceable_lines(self, final=False):
    #     invoiceable_line_ids = []
    #
    #     for line in self.order_line:
    #         invoiceable_line_ids.append(line.id)
    #
    #     return self.env['sale.order.line'].browse(invoiceable_line_ids)


    # def _prepare_invoice_line(self, **optional_values):
    #     """
    #     Prepare the dict of values to create the new invoice line for a sales order line.
    #
    #     :param qty: float quantity to invoice
    #     :param optional_values: any parameter that should be added to the returned invoice line
    #     """
    #     self.ensure_one()
    #     sale_order = self.sale_id
    #     res = {
    #         'display_type': sale_order.display_type,
    #         'sequence': sale_order.sequence,
    #         'name': sale_order.name,
    #         'product_id': self.product_id.id,
    #         'product_uom_id': self.product_uom.id,
    #         'quantity': self.qty_to_invoice,
    #         'discount': self.discount,
    #         'price_unit': self.price_unit,
    #         'tax_ids': [(6, 0, self.tax_id.ids)],
    #         'analytic_account_id': self.order_id.analytic_account_id.id,
    #         'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
    #         'sale_line_ids': [(4, self.id)],
    #     }
    #     if optional_values:
    #         res.update(optional_values)
    #     if self.display_type:
    #         res['account_id'] = False
    #     return res

    # def _create_refund_invoices(self, grouped=False, final=False, date=None):
    #
    #     # 1) Create refund invoices.
    #     invoice_vals_list = []
    #     invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
    #     for move_id in self.move_ids_without_package:
    #         picking_line = picking_line.with_company(self.company_id)
    #
    #         invoice_vals = self._prepare_refund_invoice()
    #         invoiceable_lines = self._get_invoiceable_lines(final)
    #
    #         if not any(not line.display_type for line in invoiceable_lines):
    #             raise UserError('No Invoiceable Lines')
    #
    #         invoice_line_vals = []
    #         for line in invoiceable_lines:
    #             invoice_line_vals.append(
    #                 (0, 0, line._prepare_invoice_line(
    #                     sequence=invoice_item_sequence,
    #                 )),
    #             )
    #             invoice_item_sequence += 1
    #
    #         invoice_vals['invoice_line_ids'] += invoice_line_vals
    #         invoice_vals_list.append(invoice_vals)
    #
    #     if not invoice_vals_list:
    #         raise self._nothing_to_invoice_error()
    #
    #     # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
    #     if not grouped:
    #         new_invoice_vals_list = []
    #         invoice_grouping_keys = self._get_invoice_grouping_keys()
    #         for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
    #             origins = set()
    #             payment_refs = set()
    #             refs = set()
    #             ref_invoice_vals = None
    #             for invoice_vals in invoices:
    #                 if not ref_invoice_vals:
    #                     ref_invoice_vals = invoice_vals
    #                 else:
    #                     ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
    #                 origins.add(invoice_vals['invoice_origin'])
    #                 payment_refs.add(invoice_vals['payment_reference'])
    #                 refs.add(invoice_vals['ref'])
    #             ref_invoice_vals.update({
    #                 'ref': ', '.join(refs)[:2000],
    #                 'invoice_origin': ', '.join(origins),
    #                 'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
    #             })
    #             new_invoice_vals_list.append(ref_invoice_vals)
    #         invoice_vals_list = new_invoice_vals_list
    #
    #     # 3) Create invoices.
    #
    #     # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
    #     # in a single invoice. Example:
    #     # SO 1:
    #     # - Section A (sequence: 10)
    #     # - Product A (sequence: 11)
    #     # SO 2:
    #     # - Section B (sequence: 10)
    #     # - Product B (sequence: 11)
    #     #
    #     # If SO 1 & 2 are grouped in the same invoice, the result will be:
    #     # - Section A (sequence: 10)
    #     # - Section B (sequence: 10)
    #     # - Product A (sequence: 11)
    #     # - Product B (sequence: 11)
    #     #
    #     # Resequencing should be safe, however we resequence only if there are less invoices than
    #     # orders, meaning a grouping might have been done. This could also mean that only a part
    #     # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
    #     if len(invoice_vals_list) < len(self):
    #         SaleOrderLine = self.env['sale.order.line']
    #         for invoice in invoice_vals_list:
    #             sequence = 1
    #             for line in invoice['invoice_line_ids']:
    #                 line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
    #                 sequence += 1
    #
    #     # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
    #     # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
    #     moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)
    #
    #     # 4) Some moves might actually be refunds: convert them if the total amount is negative
    #     # We do this after the moves have been created since we need taxes, etc. to know if the total
    #     # is actually negative or not
    #     if final:
    #         moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
    #     for move in moves:
    #         move.message_post_with_view('mail.message_origin_link',
    #             values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
    #             subtype_id=self.env.ref('mail.mt_note').id
    #         )
    #     return moves



    @api.depends('purchase_id')
    def _compute_po_count(self):
        for rec in self:
            rec.po_count = len(rec.purchase_id)

    @api.depends('sale_id')
    def _compute_so_count(self):
        for rec in self:
            rec.so_count = len(rec.sale_id)

    def btn_view_po(self):
        action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_form_action")
        action['views'] = [
            (self.env.ref('purchase.purchase_order_view_tree').id, 'tree'),
        ]
        action['context'] = self.env.context
        po_ids = self.mapped('purchase_id')
        action['domain'] = [('id', 'in',  [x.id for x in self.purchase_id])]

        if len(po_ids) > 1:
            action['domain'] = [('id', 'in',  [x.id for x in self.purchase_id])]
        elif len(po_ids) == 1:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form'),]
            action['res_id'] = self.purchase_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def btn_view_so(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action['views'] = [
            (self.env.ref('sale.view_order_tree').id, 'tree'),
        ]
        action['context'] = self.env.context
        sale_id = self.mapped('sale_id')
        action['domain'] = [('id', 'in',  [x.id for x in self.sale_id])]

        if len(sale_id) > 1:
            action['domain'] = [('id', 'in',  [x.id for x in self.sale_id])]
        elif len(sale_id) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form'),]
            action['res_id'] = sale_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def btn_view_invoices(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['views'] = [
            (self.env.ref('account.view_invoice_tree').id, 'tree'),
        ]
        action['context'] = self.env.context
        invoice_ids = self.mapped('invoice_id')
        action['domain'] = [('id', 'in', invoice_ids.ids)]

        if len(invoice_ids) > 1:
            action['domain'] = [('id', 'in', invoice_ids.ids)]
        elif len(invoice_ids) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form'),]
            action['res_id'] = invoice_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.depends('invoice_id')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_id)



    invoice_id = fields.Many2one('account.move' , copy=False)
    invoice_count = fields.Integer(compute="_compute_invoice_count", string='# of Invoices', copy=False, default=0, store=True)
    purchase_id = fields.Many2one('purchase.order', string="Purchase Order" ,copy=False,)
    po_count = fields.Integer(compute="_compute_po_count", string='# of Purchase Orders', copy=False, default=0, store=True)
    sale_id = fields.Many2one('sale.order',  string="Sale Order"  ,copy=False,)
    so_count = fields.Integer(compute="_compute_so_count", string='# of Sales Orders', copy=False, default=0, store=True)
    location_id = fields.Many2one('stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_src_id,
        check_company=True, readonly=True, required=True,
        states={'draft': [('readonly', False)], 'waiting': [('readonly', False)], 'confirmed': [('readonly', False)],
                'assigned': [('readonly', False)]})
    location_dest_id = fields.Many2one('stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_dest_id,
        check_company=True, readonly=True, required=True,
        states={'draft': [('readonly', False)], 'waiting': [('readonly', False)], 'confirmed': [('readonly', False)],
                'assigned': [('readonly', False)]})


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    def send_grp_email(self, grp_name, subject, msg):
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref(grp_name)
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)
        if partn_ids:
            # self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partn_ids, subtype_xmlid='mail.mt_comment',
                              force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))


    def btn_request_approval(self):
        if self.state == 'done':
            raise UserError('Sorry, the record has already been approved')
        if self.state == 'cancel':
            raise UserError('Sorry, the record is cancelled')
        msg = 'Landed Cost (%s) from %s requires your approval' % (self.name, self.env.user.name)
        self.send_grp_email(grp_name='kin_stock.group_landed_cost_receive_request_approval_email', subject=msg, msg=msg)
        self.is_request_approval_sent = True
        self.is_request_approval_by = self.env.user
        self.is_request_approval_date = fields.Datetime.now()


    is_request_approval_sent = fields.Boolean(string='Is Request Approval Sent', copy=False, tracking=True)
    is_request_approval_by = fields.Many2one('res.users', string='Requested By', copy=False, tracking=True)
    is_request_approval_date = fields.Datetime(string='Request Approval Date', copy=False, tracking=True)


class StockLandedCostLine(models.Model):
    _inherit = 'stock.landed.cost.lines'

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.name = self.product_id.name or ''
        self.split_method = self.product_id.product_tmpl_id.split_method_landed_cost or self.split_method or 'equal'
        self.price_unit = self.product_id.standard_price or 0.0
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
        self.account_id = accounts_data['expense'] or accounts_data['stock_input']