# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017-2021  Kinsolve Solutions
# Copyright 2017-2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from itertools import groupby

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero, float_compare,float_round, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import *
from urllib.parse import urlencode
from urllib.parse import urljoin
from odoo.exceptions import AccessError, UserError, ValidationError




class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_depot_type = fields.Boolean(string="Depot Type")
    is_indepot = fields.Boolean(string="Is In-Depot")
    is_exdepot = fields.Boolean(string="Is Ex-Depot")
    is_throughput = fields.Boolean(string="Is Throughput")
    is_throughput_parent_view = fields.Boolean(string="Is Throughput Parent View",help='Only One Location Should be Selected')
    is_throughput_vendor_location  = fields.Boolean(string="Throughput Vendor Location",help='Only One Location Should be Selected')
    is_oper_loss_location = fields.Boolean(string='Operational Loss Location')
    is_default_in_depot_source_location = fields.Boolean(string='Is Default In Depot Source Location',help='Only One Location Should be Selected')
    is_internal_use = fields.Boolean(string="Is Internal Use")
    is_internal_use_source_location = fields.Boolean(string="Is Internal Use Source Location")
    is_internal_use_destination_location = fields.Boolean(string="Is Internal Use Destination Location")
    is_internal_use_partner_id = fields.Many2one('res.partner',string='Internal Use Source Partner',help='The Company incurring the expense transfer')


class StockMoveLoading(models.Model):
    _inherit = 'stock.move'

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        self.ensure_one()
        # apply putaway
        location_dest_id = self.location_dest_id._get_putaway_strategy(self.product_id).id or self.location_dest_id.id
        vals = {
            'move_id': self.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'location_id': self.location_id.id,
            'location_dest_id': location_dest_id,
            'picking_id': self.picking_id.id,
            'company_id': self.company_id.id,
        }

        if quantity:
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            uom_quantity = self.product_id.uom_id._compute_quantity(quantity, self.product_uom,
                                                                    rounding_method='HALF-UP')
            uom_quantity = float_round(uom_quantity, precision_digits=rounding)
            uom_quantity_back_to_product_uom = self.product_uom._compute_quantity(uom_quantity, self.product_id.uom_id,
                                                                                  rounding_method='HALF-UP')
            if float_compare(quantity, uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
                vals = dict(vals, product_uom_qty=uom_quantity,qty_done=uom_quantity)
            else:
                vals = dict(vals, product_uom_qty=quantity,qty_done=uom_quantity, product_uom_id=self.product_id.uom_id.id)
        if reserved_quant:
            vals = dict(
                vals,
                location_id=reserved_quant.location_id.id,
                lot_id=reserved_quant.lot_id.id or False,
                package_id=reserved_quant.package_id.id or False,
                owner_id=reserved_quant.owner_id.id or False,
            )
        return vals

    def _assign_picking(self):
        """ Try to assign the moves to an existing picking that has not been
        reserved yet and has the same procurement group, locations and picking
        type (moves should already have them identical). Otherwise, create a new
        picking to assign them to. """
        Picking = self.env['stock.picking']
        grouped_moves = groupby(sorted(self, key=lambda m: [f.id for f in m._key_assign_picking()]), key=lambda m: [m._key_assign_picking()])
        for group, moves in grouped_moves:
            moves = self.env['stock.move'].concat(*list(moves))
            new_picking = False
            # Could pass the arguments contained in group but they are the same
            # for each move that why moves[0] is acceptable
            picking = False
            if picking:
                if any(picking.partner_id.id != m.partner_id.id or
                        picking.origin != m.origin for m in moves):
                    # If a picking is found, we'll append `move` to its move list and thus its
                    # `partner_id` and `ref` field will refer to multiple records. In this
                    # case, we chose to  wipe them.
                    picking.write({
                        'partner_id': False,
                        'origin': False,
                    })
            else:
                new_picking = True
                picking = Picking.create(moves._get_new_picking_values())

            moves.write({'picking_id': picking.id})
            moves._assign_picking_post_process(new=new_picking)
        return True

    def write(self,vals):
        res = super(StockMoveLoading, self).write(vals)
        picking_id = vals.get('picking_id',False)
        if picking_id:
            # see: ../addons/stock/stock.py:821
            # Change locations of moves if those of the picking change
            picking_obj = self.env['stock.picking'].browse(picking_id)
            location_id = picking_obj.location_id
            location_dest_id = picking_obj.location_dest_id
            picking_obj.write({'location_id':location_id.id,'location_dest_id': location_dest_id.id})
        return res

    @api.model
    def create(self, vals):
        location_id = self.env.context.get('atl_depot_id', False)
        location_dest_id = self.env.context.get('depot_id', False)
        if location_id :
            vals['location_id'] = location_id
        if location_dest_id :
            vals['location_dest_id'] = location_dest_id

        res = super(StockMoveLoading,self).create(vals)
        return res


    def _picking_assign(self, cr, uid, move_ids, context=None):
        """Try to assign the moves to an existing picking
        that has not been reserved yet and has the same
        procurement group, locations and picking type  (moves should already have them identical)
         Otherwise, create a new picking to assign them to.
        """
        move = self.browse(cr, uid, move_ids, context=context)[0]
        pick_obj = self.pool.get("stock.picking")

        is_load_ticket_btn = context.get('is_load_ticket_btn',False)
        if is_load_ticket_btn:
            values = self._prepare_picking_assign(cr, uid, move, context=context)
            pick = pick_obj.create(cr, uid, values, context=context)
        else:
            picks = pick_obj.search(cr, uid, [
                ('group_id', '=', move.group_id.id),
                ('location_id', '=', move.location_id.id),
                ('location_dest_id', '=', move.location_dest_id.id),
                ('picking_type_id', '=', move.picking_type_id.id),
                ('printed', '=', False),
                ('state', 'in', ['draft', 'confirmed', 'waiting', 'partially_available', 'assigned'])], limit=1,
                                    context=context)
            if picks:
                pick = picks[0]
            else:
                values = self._prepare_picking_assign(cr, uid, move, context=context)
                pick = pick_obj.create(cr, uid, values, context=context)
        res = self.write(cr, uid, move_ids, {'picking_id': pick}, context=context)
        move_id = self.browse(cr, uid, move_ids, context=context)
        move_id.picking_id._compute_ticket_param()
        return res

    throughput_receipt_movement_id = fields.Many2one('kin.throughput.receipt', string="Throughput Receipt Movement", readonly=True)
    throughput_so_transfer_movement_id = fields.Many2one('sale.order', string="Throughput Sales Order Transfer", readonly=True)


class StockPickingExtend(models.Model):
    _inherit = 'stock.picking'
    _description = "Loading/Waybill"

    # @api.model
    # def unlink_action(self):
    #     # ticket_template = self.env.ref('kin_loading.report_loading_ticket')
    #     # report_ticket_obj = self.env['ir.actions.report.xml'].browse(ticket_template.id)
    #     # self.env['ir.values'].unlink(
    #     # if report_ticket_obj.ir_values_id:
    #     #     report_ticket_obj.ir_values_id.sudo().unlink()
    #     waybill_action_template = self.env.ref('kin_loading.action_report_loading_waybill')
    #     report_waybill_obj = self.env['ir.actions.report.xml'].browse(waybill_action_template.id)
    #     if report_waybill_obj.ir_values_id:
    #         waybill_action_template.ir_values_id.sudo().unlink()
    #
    #     return True


    def _get_defferred_revenue_deduction_line(self):
        inv_line_adv = []
        for stock_move in self.move_lines:
            sale_order_line_id = stock_move.sale_line_id
            # Move from deferred revenue to sales revenue
            if sale_order_line_id.order_id.is_has_advance_invoice:
                product_deferred_revenue_id = sale_order_line_id.product_id.product_deferred_revenue_id
                if not product_deferred_revenue_id:
                    raise UserError(_('Please Define a Deferred Revenue Product for the %s, on the Product Page' % (
                        sale_order_line_id.product_id.name)))

                account = product_deferred_revenue_id.account_unearned_revenue_id or product_deferred_revenue_id.categ_id.account_unearned_revenue_id
                if not account:
                    raise UserError(_(
                        'Please define unearned revenue account for this product: "%s" (id:%d) - or for its category: "%s".') % (
                                        product_deferred_revenue_id.name, product_deferred_revenue_id.id,
                                        product_deferred_revenue_id.categ_id.name))

                fpos = sale_order_line_id.order_id.fiscal_position_id or sale_order_line_id.order_id.partner_id.property_account_position_id
                if fpos:
                    account = fpos.map_account(account)

                default_analytic_account = self.env['account.analytic.default'].account_get(
                    product_id=sale_order_line_id.product_id.id,
                    partner_id=sale_order_line_id.order_id.partner_id.id,
                    account_id=account.id,
                    user_id=sale_order_line_id.order_id.user_id.id,
                    date=date.today(),
                    company_id=sale_order_line_id.company_id.id
                )

                amount = sale_order_line_id.price_total / sale_order_line_id.product_uom_qty
                if amount <= 0.00:
                    raise UserError(_('The value of the down payment amount must be positive.'))

                unearned_taxes = sale_order_line_id.product_id.taxes_id
                if sale_order_line_id.order_id.fiscal_position_id and unearned_taxes:
                    tax_ids = sale_order_line_id.order_id.fiscal_position_id.map_tax(unearned_taxes).ids
                else:
                    tax_ids = unearned_taxes.ids

                line_adv = {
                    'name': _(" %s Move Unearned Revenue to Sales Revenue of %s for %s") % (
                    stock_move.product_id.name, amount * -stock_move.product_qty,
                    sale_order_line_id.order_id.name),
                    'sequence': sale_order_line_id.sequence,
                    'ref': sale_order_line_id.order_id.name,
                    'account_id': account.id,
                    'price_unit': amount,
                    'quantity': -stock_move.product_qty,
                    'discount': 0.0,
                    'product_uom_id': stock_move.product_uom.id,
                    'product_id': product_deferred_revenue_id.id, # This causes the validated invoice to create COG entries from Goods Dispatched
                    'tax_ids': [(6, 0, tax_ids)],
                    'analytic_account_id': default_analytic_account and default_analytic_account.analytic_id.id,
                    'sale_line_ids': [(6, 0, [sale_order_line_id.id])]  # Never remove this sale_line_ids. This determines the cost of goods sold using the FIFO and not from the product page
                }
            inv_line_adv.append(line_adv)
        return inv_line_adv

    def _get_invoiceable_lines(self):
        invoiceable_line_ids = []
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for stock_move in self.move_lines:
            sale_order_line_id = stock_move.sale_line_id

            if not sale_order_line_id:
                raise UserError(
                    _('Sorry, Dispatch cannot be validated and invoice cannot be generated, since no sales order line is linked to the stock move'))

            if not float_is_zero(stock_move.product_qty, precision_digits=precision):
                account = sale_order_line_id.product_id.property_account_income_id or sale_order_line_id.product_id.categ_id.property_account_income_categ_id
                if not account:
                    raise UserError(
                        _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % (
                        sale_order_line_id.product_id.name, sale_order_line_id.product_id.id,
                        sale_order_line_id.product_id.categ_id.name))

                fpos = sale_order_line_id.order_id.fiscal_position_id or sale_order_line_id.order_id.partner_id.property_account_position_id
                if fpos:
                    account = fpos.map_account(account)

                default_analytic_account = self.env['account.analytic.default'].account_get(
                    product_id=sale_order_line_id.product_id.id,
                    partner_id=sale_order_line_id.order_id.partner_id.id ,
                    account_id=account.id,
                    user_id=sale_order_line_id.order_id.user_id.id,
                    date=date.today(),
                    company_id=sale_order_line_id.company_id.id
                )

                inv_line = {
                    'name': sale_order_line_id.name,
                    'sequence': sale_order_line_id.sequence,
                    'ref': sale_order_line_id.order_id.name,
                    'account_id': account.id,
                    'price_unit': sale_order_line_id.price_unit,
                    'quantity': stock_move.product_qty,
                    'discount': sale_order_line_id.discount,
                    'product_uom_id': stock_move.product_uom.id,
                    'product_id': stock_move.product_id.id or False,
                    'tax_ids': [(6, 0, sale_order_line_id.tax_id.ids)],
                    'analytic_account_id':  default_analytic_account and default_analytic_account.analytic_id.id,
                    'sale_line_ids': [(6, 0, [sale_order_line_id.id])] # Never remove this sale_line_ids. This determines the cost of goods sold using the FIFO and not from the product page
                }
            invoiceable_line_ids.append(inv_line)

        return invoiceable_line_ids


    def _create_final_invoice_depot(self,grouped=False, final=False):
        order = self.sale_id
        # 1) Create invoices.
        invoice_vals_list = []
        order = order.with_company(order.company_id)

        invoice_vals = order._prepare_invoice()
        invoice_vals['is_from_inventory'] = True
        invoice_line_vals = self._get_invoiceable_lines()
        invoice_vals['invoice_line_ids'] += invoice_line_vals
        inv_line_def_vals = self._get_defferred_revenue_deduction_line()
        invoice_vals['invoice_line_ids'] += inv_line_def_vals
        invoice_vals_list.append(invoice_vals)

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                subtype_id=self.env.ref('mail.mt_note').id
            )
            move.is_has_advance_invoice = True
            move.picking_id = self
            self.invoice_id = move
        moves.action_post()
        return moves



    @api.onchange('dest_depot_type_id')
    def onchange_dest_depot_type_id(self):
        self.location_dest_id = False


    @api.onchange('source_depot_type_id')
    def onchange_source_depot_type_id(self):
        self.location_id = False

    

    
    def action_ticket_recovered(self):
        action = self.env["ir.actions.actions"]._for_xml_id("kin_loading.action_ticket_recovered")

        return {
            'name': action['name'],
            'help': action['help'],
            'type': action['type'],
            'views': [(self.env.ref('kin_loading.view_ticket_recovered').id, 'form'),],
            'target': action['target'],
            'domain': action['domain'],
            'res_model': action['res_model'],
            'target': 'new'
        }






    
    def action_cancel(self):
        res = super(StockPickingExtend,self).action_cancel()
        sale_order = self.sale_id
        if sale_order:
            for line in sale_order.order_line:
                line.ticket_created_qty -= self.ticket_load_qty
                line._compute_procurement_qty()
        return res


    
    def btn_block_ticket(self,msg):
        if self.state == 'cancel':
            raise UserError(_('No need for the block, since Loading Ticket is already cancelled'))
        self.is_block_ticket = True
        self.block_reason = msg
        self.block_date = datetime.today()
        self.block_user_id = self.env.user

        user_ids = []
        group_obj = self.env.ref('kin_loading.group_receive_block_ticket_notification')
        for user in group_obj.users:
            user_ids.append(user.partner_id.id)

            self.message_post(_(
                'The Loading Ticket (%s), belonging to %s, has been blocked by %s, with reason: %s.') % (
                                  self.name, self.partner_id.name, self.env.user.name,self.block_reason),
                              subject='A Loading Ticket has been blocked', partner_ids=[user_ids],
                              subtype_xmlid='mail.mt_comment', force_send=False)

        return

    
    def btn_unblock_ticket(self,msg):
        if self.state == 'cancel':
            raise UserError(_('No need for the block, since Loading Ticket is already cancelled'))
        self.is_block_ticket = False
        self.unblock_reason = msg
        self.unblock_date = datetime.today()
        self.unblock_user_id = self.env.user

        user_ids = []
        group_obj = self.env.ref('kin_loading.group_receive_block_ticket_notification')
        for user in group_obj.users:
            user_ids.append(user.partner_id.id)

            self.message_post(_(
                'The Loading Ticket (%s), belonging to %s, has been Unblocked by %s, with reason: %s.') % (
                                  self.name, self.partner_id.name, self.env.user.name,self.unblock_reason),
                              subject='A Loading Ticket has been Unblocked', partner_ids=[user_ids],
                              subtype_xmlid='mail.mt_comment', force_send=False)
        return

    
    def btn_print_loading_ticket(self):
        raise UserError('This report needs to be implemented in a sub module')
        return

    
    def btn_print_waybill(self):
        raise UserError('This report needs to be implemented in a sub module')
        return

    def button_validate(self):
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        #check if the loading programme is done
        if self.is_loading_ticket == True:
            if not self.loading_programme_id:
                raise UserError('Sorry, Wait for the Ticket to be Programmed before you can dispatch the goods')
            if self.loading_programme_id.state != 'approve':
                raise UserError('Sorry, you cannot dispatch this goods, because the loading programme is in %s state' % (self.loading_programme_id.state))

        if self.is_loading_ticket or self.is_exdepot_ticket or self.is_throughput_ticket or self.is_internal_use_ticket:
            self.waybill_no = self.env['ir.sequence'].next_by_code('waybill_id')

            if self.is_throughput_ticket :
                self.waybill_no  = self.env['ir.sequence'].next_by_code('thru_delv_code')

            if self.is_internal_use_ticket:
                self.waybill_no = self.env['ir.sequence'].next_by_code('intu_delv_code')

            if self.is_block_ticket :
                raise UserError(_("Sorry, Ticket is currently blocked and cannot be Dispatched"))

            if not self.is_exdepot_ticket and self.picking_type_code == 'outgoing' and self.sale_id and self.ticket_load_qty != self.total_dispatch_qty  :
                raise UserError(_('The Total Dispatched Qty. Must be Equal the Requested Ticket Load Qty. Please Check your Compartment Qty.'))

        # Sanity checks.
        pickings_without_moves = self.browse()
        pickings_without_quantities = self.browse()
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']
        for picking in self:
            if self.is_loading_ticket == True:
                picking.move_line_ids_without_package.unlink()
                picking.action_assign()
            if not picking.move_lines and not picking.move_line_ids:
                pickings_without_moves |= picking

            picking.message_subscribe([self.env.user.partner_id.id])
            picking_type = picking.picking_type_id
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
            no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in picking.move_line_ids)
            if no_reserved_quantities and no_quantities_done:
                pickings_without_quantities |= picking

            if picking_type.use_create_lots or picking_type.use_existing_lots:
                lines_to_check = picking.move_line_ids
                if not no_quantities_done:
                    lines_to_check = lines_to_check.filtered(lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
                for line in lines_to_check:
                    product = line.product_id
                    if product and product.tracking != 'none':
                        if not line.lot_name and not line.lot_id:
                            pickings_without_lots |= picking
                            products_without_lots |= product

        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(_('Please add some items to move.'))
            if pickings_without_quantities:
                raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                raise UserError(_('You need to set a Vessel name for products %s.') % ', '.join(products_without_lots.mapped('display_name')))
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.') % ', '.join(pickings_without_moves.mapped('name'))
            if pickings_without_quantities:
                message += _('\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To force these transfers, switch in edit more and encode the done quantities.') % ', '.join(pickings_without_quantities.mapped('name'))
            if pickings_without_lots:
                message += _('\n\nTransfers %s: You need to set a Vessel name for products %s.') % (', '.join(pickings_without_lots.mapped('name')), ', '.join(products_without_lots.mapped('display_name')))
            if message:
                raise UserError(message.lstrip())

        # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
        # moves and/or the context and never call `_action_done`.
        if not self.env.context.get('button_validate_picking_ids'):
            self = self.with_context(button_validate_picking_ids=self.ids)
        res = self._pre_action_done_hook()
        if res is not True:
            return res

        # Call `_action_done`.
        if self.env.context.get('picking_ids_not_to_backorder'):
            pickings_not_to_backorder = self.browse(self.env.context['picking_ids_not_to_backorder'])
            pickings_to_backorder = self - pickings_not_to_backorder
        else:
            pickings_not_to_backorder = self.env['stock.picking']
            pickings_to_backorder = self
        pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
        pickings_to_backorder.with_context(cancel_backorder=False)._action_done()

        self._create_final_invoice_depot()
        return True


    def check_backorder(self, cr, uid, picking, context=None):
        res = super(StockPickingExtend,self).check_backorder(cr, uid, picking, context)
        if res and picking.picking_type_code == 'outgoing' and picking.sale_id :
            raise UserError(_('Please the "Done" Qty. Must be Equal to the "To Do" Qty in the operation lines'))
        return res

    #incase there is need for backorder. The process flow for delivery may not come here at all
    # def _create_backorder(self, cr, uid, picking, backorder_moves=[], context=None):
    #     res = super(StockPickingExtend,self)._create_backorder(cr, uid, picking, backorder_moves=[], context=context)
    #     if res :
    #         backorder_obj = self.browse(cr, uid, res, context=context)
    #         backorder_obj.loading_programme_id = False
    #     return res




    
    # def do_new_transfer(self):
    #
    #     if self.picking_type_code != 'outgoing':
    #         for pack_operation in self.pack_operation_product_ids:
    #             if pack_operation.qty_done <= 0 :
    #                 raise UserError(_('Qty Done should be Set on the lines'))
    #
    #     if self.picking_type_code == 'outgoing' and self.is_loading_ticket  :
    #         order = self.sale_id
    #         if order.is_cancelled_order:
    #             raise UserError(_('The Sales Order for this Ticket has been Cancelled, so this ticket cannot be dispatched. Please contact the Admin'))
    #
    #         if len(order.invoice_ids) == 0 and not order.is_throughput_order and not order.is_internal_use_order :
    #             raise UserError(_('No Advance Payment Invoice for this Order. Please Contact the Admin'))
    #
    #         if not order.is_has_advance_invoice and not order.is_throughput_order and not order.is_internal_use_order :
    #             raise UserError(_('No Advance Payment Invoice. Please Contact the Admin'))
    #
    #         if order.is_cancelled_invoice:
    #             raise UserError(
    #                     _('Advance Payment Invoice for this Sales Order attached to this loading ticket, has been Cancelled. Please contact the admin'))
    #
    #         if not order.is_advance_invoice_validated and not order.is_throughput_order and not order.is_internal_use_order :
    #                 raise UserError(_(
    #                     "Please contact the accountant to validate the invoice before dispatching the goods for the sales order: %s, belonging to %s" % (
    #                         order.name, order.partner_id.name)))
    #
    #         if not self.loading_programme_id :
    #             raise UserError(_(
    #                 'The loading ticket is not included in any of the loading programme'))
    #
    #
    #         if not self.loaded_date:
    #             raise UserError(_('Please set the Loaded Date below before validating this record'))
    #
    #         if not self.truck_no:
    #             raise UserError(_('Please set the Truck Number below before validating this record'))
    #
    #         if not self.receiving_station_address:
    #             raise UserError(_('Please set the Receiving Station Address below before validating this record'))
    #
    #         if not self.dpr_no:
    #             raise UserError(_('Please set the DPR Number below before validating this record'))
    #
    #         if not self.location_addr_id:
    #             raise UserError(_('Please set the Location below before validating this record'))
    #
    #
    #     return super(StockPickingExtend,self).do_new_transfer()




    def transfer_create_invoice_loading_ticket(self):

        inv_obj = self.create_customer_invoice_loading_ticket()
        inv_id = inv_obj.id

        if inv_obj:  # if inv_id is empty , maybe as a result of an already created invoice, thus no invoice may be created here. This can happen when sales order is cancelled and open again with another delivery that creates an invoice

            if self.picking_type_id.is_validate_invoice:
                # #this one below dis npt work because it could not allow payment allocation after opening the invoice and also it could not allow making a zero total amout invoice to paid automatically
                # inv_obj.action_move_create()
                # inv_obj.invoice_validate()
                inv_obj.action_post()

            inv_obj.sale_id = self.sale_id
            inv_obj.picking_id = self
            self.invoice_id = inv_obj

            user_ids = []
            if inv_obj.partner_id and inv_obj.partner_id.user_id:
                user_ids.append(inv_obj.partner_id.user_id.id)

            # Send Invoice Notification to Selected Users
            is_send_invoice_notification = self.picking_type_id.is_send_invoice_notification
            company_email = self.env.user.company_id.email.strip()
            if is_send_invoice_notification and company_email:
                # Custom Email Template
                mail_template = self.env.ref('kin_stock.mail_templ_invoice_delivery')
                the_url = inv_obj._get_url('account', 'menu_action_invoice_tree1', 'action_invoice_tree1')

                users = []
                group_obj = self.env.ref('kin_stock.group_receive_inventory_invoice_email')
                for user in group_obj.users:
                    users.append(user.id)
                    if user.partner_id.email and user.partner_id.email.strip():
                        ctx = {'system_email': company_email,
                               'accountant_email': user.partner_id.email,
                               'accountant_name': user.partner_id.name,
                               'url': the_url,
                               'origin': inv_obj.origin,
                               'partner_name': self.partner_id.name
                               }
                        mail_template.with_context(ctx).send_mail(self.id, force_send=False)
                        self.show_alert_box = True

                # Also notify uses of items awaiting pickup
                stock_person_email = self.env.user.partner_id.email.strip()
                stock_person_name = self.env.user.name

                if company_email and stock_person_email:
                    # Custom Email Template
                    mail_template = self.env.ref('kin_stock.mail_templ_delivery_awaiting_pickup')
                    ctx = {}
                    ctx.update({'picking_id': self.id})
                    the_url = self._get_stock_url('stock', 'all_picking', 'action_picking_tree_all', ctx)

                    user_ids = []
                    group_obj = self.env.ref('kin_stock.group_receive_stock_delivery_orders_awaiting_pickup_email')
                    for user in group_obj.users:
                        if user.partner_id.email and user.partner_id.email.strip():
                            user_ids.append(user.id)
                            ctx = {'system_email': company_email,
                                   'stock_person_name': stock_person_name,
                                   'stock_person_email': stock_person_email,
                                   'notify_person_email': user.partner_id.email,
                                   'notify_person_name': user.partner_id.name,
                                   'url': the_url
                                   }
                            mail_template.with_context(ctx).send_mail(self.id, force_send=False)
                            # self.message_subscribe_users(user_ids=user_ids)



    
    def do_transfer(self):
        if not self.is_throughput_ticket:

            sale_order = self.sale_id
            picking_type_code = self.picking_type_code
            invoic_obj = self.invoice_id or False
            if picking_type_code == "incoming" and sale_order and invoic_obj:  # Create a Customer refund invoice
                self.transfer_create_refund_invoice()  # return inwards

            is_delivery_invoicing_policy = False
            backorder = self.backorder_id

            # for picking_line in self.pack_operation_ids:
            #     if picking_line.product_id.invoice_policy == "delivery":
            #         is_delivery_invoicing_policy = True  # if at least one picking line product invoicing policy is based on delivered quantity

            # if backorder and not is_delivery_invoicing_policy:  # Don't create the invoice, if it is a backorder and the invoicing policy is based on ordered quantity
            #     return res

            if picking_type_code == "outgoing" and sale_order:  # Create a Customer Invoice
                self.transfer_create_invoice_loading_ticket()

                ############################################################################################
                ######   FOR PURCHASES VENDOR BILLS AND PURCHASE RETURNS

            is_received_purchase_method = False
            backorder = self.backorder_id

            for picking_line in self.pack_operation_ids:
                if picking_line.product_id.purchase_method == "receive":
                    is_received_purchase_method = True

            # if backorder and not is_received_purchase_method:  # Don't create the invoice, if it is a backorder and the purchase method is based on ordered quantity
            #     return res

            purchase_order = self.purchase_id
            if picking_type_code == "incoming" and purchase_order:  # Create a Vendor Bill
                self.transfer_create_bill()

            # Create purchase refund bill to supplier
            prev_picking_obj = self.previous_picking_id
            if prev_picking_obj:
                prev_purchase_order = prev_picking_obj.purchase_id or False
                prev_invoice_id = prev_picking_obj.invoice_id or False
                if picking_type_code == "outgoing" and prev_purchase_order and prev_invoice_id:  # Create a Return goods Invoice
                    self.transfer_create_refund_bill()






        else:
            res = super(StockPickingExtend, self).do_transfer()

        return res

    
    def write(self,vals):
        for rec in self :
            location_id = vals.get('location_id',False)
            location_dest_id = vals.get('location_dest_id', False)

            if location_id and rec.env['stock.location'].browse(location_id).is_exdepot :
                rec.write({'is_loading_ticket':True, 'is_exdepot_ticket': True, 'is_throughput_ticket': False, 'is_internal_use_ticket' : False ,'is_indepot_ticket' : False , 'is_retail_station_ticket' : False })
            elif location_id and rec.env['stock.location'].browse(location_id).is_internal_use and rec.env['stock.location'].browse(location_dest_id).is_internal_use :
                rec.write({'is_loading_ticket': True, 'is_exdepot_ticket': False, 'is_throughput_ticket': False, 'is_internal_use_ticket' : True , 'is_indepot_ticket': False, 'is_retail_station_ticket': False})
            elif location_id and rec.env['stock.location'].browse(location_id).is_indepot :
                rec.write({'is_loading_ticket': True, 'is_exdepot_ticket': False, 'is_throughput_ticket': False, 'is_internal_use_ticket' : False ,
                            'is_indepot_ticket': True, 'is_retail_station_ticket': False})
            elif location_id and rec.env['stock.location'].browse(location_id).is_throughput :
                rec.write({'is_loading_ticket': True, 'is_exdepot_ticket': False, 'is_throughput_ticket': True, 'is_internal_use_ticket' : False , 'is_indepot_ticket': False, 'is_retail_station_ticket': False})

            res = super(StockPickingExtend,rec).write(vals)
            return  res

    @api.model
    def create(self, vals):
        authorization_code = self.env.context.get('authorization_code', False)
        loading_date = self.env.context.get('loading_date', False)
        location_id = self.env.context.get('atl_depot_id', False)
        destination_id = self.env.context.get('depot_id',False)

        if location_id :
            vals['location_id'] = location_id

        if destination_id :
            vals['location_dest_id'] = destination_id

        if authorization_code:
            vals['authorization_form_no'] = authorization_code

        if loading_date :
            #vals['min_date'] = loading_date.strftime('%Y-%m-%d') # This works too, but i wanted date object to be assigned directly to min_date
            vals['min_date'] = loading_date


        is_load_ticket_btn = self.env.context.get('is_load_ticket_btn', False)
        if is_load_ticket_btn:
            default_location = self.env.ref('kin_loading.default_stock_location_loading')
            vals['is_loading_ticket'] =  True
            vals['is_indepot_ticket'] = True
            vals['source_depot_type_id'] = default_location.id


            if vals['is_indepot_ticket'] :
                in_depot_default_source_location = self.env['stock.location'].search([('is_default_in_depot_source_location', '=', True)], limit=1)
                if in_depot_default_source_location :
                    vals['location_id'] = in_depot_default_source_location.id
                    vals['source_depot_type_id'] = in_depot_default_source_location.location_id.id


            is_throughput_so = self.env.context.get('is_throughput_so', False)
            if is_throughput_so:
                partner_id = self.env['res.partner'].browse(vals['partner_id'])
                throughput_location = partner_id.throughput_location_id
                if not throughput_location:
                    raise UserError('Please Contact the Admin to Set the Throughput Location for the Customer')

                vals['location_id'] = throughput_location.id
                vals['source_depot_type_id'] = throughput_location.location_id.id
                vals.update({'is_loading_ticket': True, 'is_exdepot_ticket': False, 'is_throughput_ticket': True, 'is_internal_use_ticket': False,
                            'is_indepot_ticket': False, 'is_retail_station_ticket': False})


            is_internal_use_so = self.env.context.get('is_internal_use_so', False)
            sale_order = self.env.context.get('sale_order',False)
            if is_internal_use_so and sale_order:
                kin_internal_use = sale_order.internal_use_source_id
                vals['location_id'] = kin_internal_use.source_location_id.id
                vals['source_depot_type_id'] = kin_internal_use.source_location_id.location_id.id
                vals['location_dest_id'] = kin_internal_use.destination_location_id.id
                vals['dest_depot_type_id'] = kin_internal_use.destination_location_id.location_id.id
                vals.update({'is_loading_ticket': True, 'is_exdepot_ticket': False, 'is_throughput_ticket': False, 'is_internal_use_ticket': True,
                             'is_indepot_ticket': False, 'is_retail_station_ticket': False})

        res = super(StockPickingExtend, self).create(vals)
        return res




    @api.depends('comp1_vol','comp2_vol','comp3_vol','comp4_vol','comp5_vol','comp6_vol','comp7_vol','comp8_vol')
    def _compute_ticket_param(self):
        for rec in self:
            if rec.picking_type_code == "outgoing":
                rec.product_id =  rec.move_lines and rec.move_lines[0].product_id or False
                rec.ticket_load_qty = rec.move_lines and rec.move_lines[0].product_qty or False
                rec.total_dispatch_qty = rec.comp1_vol + rec.comp2_vol + rec.comp3_vol + rec.comp4_vol + rec.comp5_vol + rec.comp6_vol + rec.comp7_vol + rec.comp8_vol





    def action_assign(self):
        is_other_sale = self.env.context.get('is_other_sale',False)
        is_load_ticket_btn = self.env.context.get('is_load_ticket_btn', False)
        # if not is_other_sale and not self.source_depot_type_id.is_depot_type and self.picking_type_code != 'incoming' and not self.is_throughput_ticket:
        #     raise UserError(_('Please Select a Source Location Type'))
        if self.source_depot_type_id.is_throughput_parent_view and not is_other_sale and self.source_depot_type_id.is_depot_type and self.picking_type_code != 'incoming' and not self.is_throughput_ticket :
            raise UserError(_('Sorry, Throughput operation is not allowed in In Depot Operation, because it will lead to zero value posting for the stock movement'))
        if is_load_ticket_btn :
            return True
        res = super(StockPickingExtend, self).action_assign()
        return res

    def _get_dpr_status(self, loading_programme_date, loading_programme):
        dpr_status = False
        programme_date = loading_programme_date or loading_programme.programme_date
        if not programme_date:
            raise UserError(
                'Please First Create a Loading Programme with a Programme Date, to check the DPR license date')
        if self.dpr_info_id.dpr_expiry_date and self.dpr_info_id.dpr_expiry_date < programme_date:
            dpr_status = 'expired'
        elif self.dpr_info_id.dpr_expiry_date and self.dpr_info_id.dpr_expiry_date >= programme_date:
            dpr_status = 'valid'
        return dpr_status

    @api.onchange('dpr_info_id')
    def _onchange_dpr_info(self):
        loading_programme_date = self.env.context.get('loading_programme_date', False)
        dpr_info_id = self.dpr_info_id
        vals = {
            'receiving_station_address': dpr_info_id.address,
            'dpr_no': dpr_info_id.dpr_no,
            'dpr_expiry_date': dpr_info_id.dpr_expiry_date,
        }
        if self.loading_programme_id or loading_programme_date:
            programme_date = False
            if loading_programme_date:
                programme_date = datetime.strptime(loading_programme_date, '%Y-%m-%d').date()
            vals['dpr_status'] = self._get_dpr_status(programme_date, self.loading_programme_id)

        # Using write() here does not work.  but direct assignments works, but not suitable,
        # Note that update() is different from Write(). Update(0 method updates on the front end. Similar to what return {'value':{}} does
        self.update(vals)

    @api.depends('move_ids_without_package.quantity_done')
    def _compute_amount_in_words(self):
        for rec in self:
            current_curr = self.env.company.currency_id
            if current_curr:
                if self.move_ids_without_package:
                    amount_in_words = current_curr.amount_to_text(
                        self.move_ids_without_package[0].quantity_done)
                    rec.amount_in_words = amount_in_words.replace(
                        'Naira', '').replace('Kobo', '') + ' Gallons'
            else:
                rec.amount_in_words = False




    meter_no = fields.Char(string='Meter No.')
    is_loading_programme_approved = fields.Boolean(string='Is Loading programme Approved')
    authorization_form_no = fields.Char(string="Authorization Form No",readonly=True)
    product_id = fields.Many2one('product.product',string='Product',compute="_compute_ticket_param",store=True)
    truck_no = fields.Char(string='Truck No.')
    ticket_date = fields.Date(string='Ticket Date',default=fields.Datetime.now)
    # quantity_required = fields.Float('Quantity Required')
    # product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    # customer_id = fields.Many2one('res.partner',"Customer's Name")
    customer_address = fields.Char(related="partner_id.street",string='Address',store=True)
    # location_addr_id = fields.Many2one('res.country.state',string="Location")
    location_addr_id = fields.Char(string="Location")
    loader_id = fields.Many2one('res.users',string="Loader's Name")
    loaded_date = fields.Date(string='Loaded Date')
    # quantity_loaded = fields.Float('Quantity Loaded')
    depot_officer_id = fields.Many2one('res.users', string="Dispatch Officer's Name")
    dispatch_date = fields.Date(string='Dispatch Date')
    supervisor_officer_id = fields.Many2one('res.users', string="Supervisor's Name")
    supervisor_date = fields.Date(string='Supervisor Date')
    dpr_no = fields.Char(string='DPR License No.')
    loading_programme_id = fields.Many2one('loading.programme',string='Approved Loading Programme',readonly=True)
    loading_programme_ids = fields.Many2many('loading.programme', 'lp_ticket', 'picking_id', 'loading_prog_id',
                                             ondelete='restrict', string='Loading Programme')
    waybill_no = fields.Char('Waybill No.',readonly=True)
    # ref_no = fields.Char('Ref. No.')
    comp1_receipt = fields.Float('1')
    comp2_receipt = fields.Float('2')
    comp3_receipt = fields.Float('3')
    comp4_receipt = fields.Float('4')
    comp5_receipt = fields.Float('5')
    comp6_receipt = fields.Float('6')
    comp7_receipt = fields.Float('7')
    comp8_receipt = fields.Float('8')
    comp1_vol = fields.Float('1')
    comp2_vol = fields.Float('2')
    comp3_vol = fields.Float('3')
    comp4_vol = fields.Float('4')
    comp5_vol = fields.Float('5')
    comp6_vol = fields.Float('6')
    comp7_vol = fields.Float('7')
    comp8_vol = fields.Float('8')
    ticket_id = fields.Char(related='name',string="Ticket")
    # supervisor_id = fields.Many2one('res.users', string="Supervisor's  Name")
    # supervisor_date = fields.Date(string="Supervisor's Date")
    driver_name = fields.Char(string="Driver's  Name")
    receiving_officer = fields.Char(string='Receiving Officer')
    depot_manager = fields.Char(string='Depot Manager')
    # driver_date = fields.Date(string="Driver's Date")
    # customer_rep_id = fields.Many2one('res.users', string="Customer's Rep.  Name")
    # customer_rep_date = fields.Date(string="Customer's Date")
    picking_type_code = fields.Selection('stock.picking.type',related='picking_type_id.code',string='Picking Type',store=True)
    is_depot_manager_approve = fields.Boolean('Depot Manager Approved')


    is_loading_ticket = fields.Boolean('Loading Ticket')
    is_indepot_ticket = fields.Boolean('In-Depot Ticket')
    is_exdepot_ticket = fields.Boolean('ExDepot Ticket')
    is_throughput_ticket = fields.Boolean('Throughput Ticket')
    is_internal_use_ticket = fields.Boolean('Internal Use Ticket')
    is_retail_station_ticket = fields.Boolean('Retail Station Ticket')
    receiving_station_address = fields.Char(string="Receiving Customer's Address")
    receiving_station_management = fields.Char(string="Receiving Station Manager")
    receiving_manager_phone = fields.Char(string="Receiving Manager's Phone")
    truck_driver_phone =  fields.Char(string="Truck Driver Phone")
    is_block_ticket = fields.Boolean(string="Block Ticket")
    block_reason = fields.Text(string="Block Reason")
    block_date = fields.Datetime('Blocked Date')
    block_user_id = fields.Many2one('res.users',string="Blocked By")
    unblock_reason = fields.Text(string="UnBlock Reason")
    unblock_date = fields.Datetime('UnBlocked Date')
    unblock_user_id = fields.Many2one('res.users', string="UnBlocked By")
    total_dispatch_qty = fields.Float(string="Total Dispatched Qty.",compute="_compute_ticket_param",store=True)
    ticket_load_qty = fields.Float(string="Ticket Qty.",compute="_compute_ticket_param",store=True)
    source_depot_type_id = fields.Many2one('stock.location',string="Source Location Type")
    dest_depot_type_id = fields.Many2one('stock.location', string="Destination Type")
    remark = fields.Text(string = "Remark")
    is_loading_ticket_printed = fields.Boolean(string='Is loading Ticket Printed')
    is_waybill_printed = fields.Boolean(string='Is Waybill Printed')
    dpr_info_id = fields.Many2one('dpr.info',string='Destination')
    dpr_status = fields.Selection(
        [('valid', 'Valid'),('expired', 'Expired'), ('renew','Under Renewal')],
         string='DPR Status')
    dpr_expiry_date = fields.Date('DPR Expiry Date')
    amount_in_words = fields.Char(
        string="Amount in Words", store=True, compute=_compute_amount_in_words)




class LoadingProgramme(models.Model):
    _name = 'loading.programme'
    _description = "Loading Programme"
    _inherit = ['mail.thread']
    _order = 'name desc'

    def send_email(self, grp_name, subject, msg):
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref(grp_name)
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)
        if partn_ids:
            # self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))


    @api.onchange('product_id')
    def _product_change(self):
        if any(ticket.product_id != self.product_id for ticket in self.ticket_ids):
            raise UserError(_("Kindly remove all the Non-%s tickets below") % (self.product_id.name))

    
    def unlink(self):
        for rec in self:
            for ticket in rec.ticket_ids:
                ticket.is_loading_programme_approved = False
            if rec.state == 'approve':
                raise UserError('Sorry, you can not delete an approved loading programme. Howver, you can reset it to draft before deleting')
        return super(LoadingProgramme, self).unlink()



    def _perform_ticket_done_check(self):
        # check if the tickets for each line has been validated
        done_tickets = []
        lines = self.ticket_ids
        for line in lines:
            if line.state == 'done':
                done_tickets.append(line.name)

        if done_tickets:
            raise UserError(_(
                "The following ticket(s) in this programme are done already. So this loading programme cannot be cancelled: \n  %s") % (
                                ', \n'.join(ticket for ticket in done_tickets)))
    
    def action_cancel(self):
        self._perform_ticket_done_check()
        for rec in self:
            for ticket in rec.ticket_ids:
                ticket.is_loading_programme_approved = False
        self.write({'state': 'cancel'})
        return

    def action_draft(self):
        self._perform_ticket_done_check()
        for rec in self:
            for ticket in rec.ticket_ids:
                ticket.is_loading_programme_approved = False
        self.write({'state': 'draft'})

    def btn_loading_programme_excel_export(self):
        return self.env.ref('kin_loading.loading_programme_excel_report').report_action(self)

    def btn_loading_programme_pdf_export(self):
        return self.env.ref('kin_loading.action_report_loading_programme').report_action(self)


    def check_blocked_tickets(self):
        for lp in self.ticket_ids:
            if lp.is_block_ticket == True:
                raise UserError(_('The Ticket with ID: %s, is already blocked. Please remove it from the loading programme' % (lp.name)))

    
    def action_confirm(self):

        if len(self.ticket_ids) <= 0 :
            raise UserError("Kindly add tickets to Programme Lines")

        if any(not ticket.dpr_info_id for ticket in self.ticket_ids):
            raise UserError('Kindly Set the Destination for each of the lines below')

        for line in self.ticket_ids:
            if not line.dpr_status:
                raise UserError('Check if the destination has been set or the DPR status field')

            if line.dpr_status == 'expired' :
                raise UserError(_('Please ensure the DPR license for the Destination on the ticket - %s is valid or under renewal status, before you can proceed.') % (line.name))

        self.check_blocked_tickets()

        for picking in self.ticket_ids :
            picking.loading_programme_id = self

        # Notify User/depot manager
        self.send_email(grp_name='kin_loading.group_depot_manager',
                        subject='A New %s Loading Programme (%s) has been Confirmed by %s for %s' % (self.product_id.name,self.name, self.env.user.name,self.programme_date),
                        msg='A New %s Loading Programme (%s) has been created and confirmed by %s for %s. Kindly approve the programme' % (self.product_id.name,self.name, self.env.user.name,self.programme_date))

        depot_officer_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return self.write({'state': 'confirm','depot_officer_id':self.env.user.id,'depot_officer_date':depot_officer_date})





    def action_approve(self):
        self.check_blocked_tickets()

        for ticket in self.ticket_ids:
            ticket.is_loading_programme_approved = True
            ticket.action_assign()

        # Notify Dispatch officers/Inventory users
        self.send_email(grp_name='kin_loading.group_dispatch_officer',
                        subject='A New %s Loading Programme (%s) has been finally approved by %s for %s' % (
                        self.product_id.name, self.name, self.env.user.name, self.programme_date),
                        msg='A New %s Loading Programme (%s) has been finally approved by %s for %s. Kindly proceed with the loading and dispatch of the goods for all the tickets in the programme' % (
                        self.product_id.name, self.name, self.env.user.name, self.programme_date))

        depot_manager_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        res = self.write({'state': 'approve', 'depot_manager_id': self.env.user.id,
                           'depot_manager_date': depot_manager_date})

        return res


    
    def action_disapprove(self, msg):
        user = self.env.user
        # Notify User/depot officer
        self.send_email(grp_name='kin_loading.group_depot_officer',
                        subject='The Loading Programme (%s) has been Dis-Approved by %s' % (
                                  self.name, user.name),
                        msg = 'The Loading Programme (%s) has been DisApproved by %s. Reason for Disapproval: %s ' % (
                                  self.name, user.name, msg))
        return self.write({'state': 'draft', 'depot_manager_disapprove_id': user.id,
                           'depot_manager_disapprove_date': datetime.today(), 'depot_manager_reason': msg})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('loading_programme_code') or 'New'
        return super(LoadingProgramme, self).create(vals)


    def btn_view_tickets(self):
        action = self.env["ir.actions.actions"]._for_xml_id("kin_loading.action_depot_dispatch")
        action['views'] = [
            (self.env.ref('kin_loading.vpicktree_depot').id, 'tree'),
            (self.env.ref('kin_loading.view_picking_depot_form').id, 'form')
        ]
        action['context'] = self.env.context
        ticket_ids = self.mapped('ticket_ids')
        action['domain'] = [('id', 'in', ticket_ids.ids)]

        if len(ticket_ids) > 1:
            action['domain'] = [('id', 'in', ticket_ids.ids)]
        elif len(ticket_ids) == 1:
            action['res_id'] = ticket_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        for rec in self:
            rec.ticket_count = len(rec.ticket_ids)

    name = fields.Char(string='Name')
    programme_date = fields.Date(string='Date',default=fields.Datetime.now)
    product_id = fields.Many2one('product.product', string='Product')
    depot_officer_id = fields.Many2one('res.users',string='Depot Officer')
    depot_officer_date = fields.Datetime(string='Depot Officer Confirmation Date')
    depot_manager_id = fields.Many2one('res.users', string='Depot Manager')
    depot_manager_date = fields.Datetime(string='Depot Manager Approval Date')
    depot_manager_disapprove_id = fields.Many2one('res.users', string='Depot Manager')
    depot_manager_disapprove_date = fields.Datetime(string='Depot Manager DisApproval Date')
    depot_manager_reason = fields.Text('Depot Manager Reason')
    ticket_ids = fields.Many2many('stock.picking', 'lp_ticket',  'loading_prog_id', 'picking_id', string='Loading Program Lines', ondelete='restrict')
    ticket_count = fields.Integer(compute="_compute_ticket_count", string='# of Tickets', copy=False, default=0)
    state = fields.Selection(
        [('draft', 'Draft'),('confirm', 'Confirmed'), ('approve', 'Approved'), ('cancel','Cancel')],
        default='draft')



class AccountMoveExtend(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        # Authorization to load
        #check for sales order that generated the advance invoice and change the state of the sales order to ATL awaiting approva;
        if self.sale_order_id:
            sale_order = self.sale_order_id
            sale_order.state = 'atl_awaiting_approval'
            sale_order.is_has_advance_invoice = True
            sale_order.is_cancelled_invoice = False
            sale_order.is_advance_invoice_validated = True

            # generate authorization code
            # order.authorization_code = self.env['ir.sequence'].next_by_code('authorization_code')

            # Notify User/depot manager for ATL
            sale_order.send_email(grp_name='kin_loading.group_receive_atl_awaiting_approval_email',
                                subject='Authorization to Load for the New Sales order with id (%s) for the customer (%s)' % (
                                    sale_order.name, sale_order.partner_id.name),
                                msg='A New Sales order document with id (%s) has been approved. You can now approve the ATL document, for Loading tickets to be created' % sale_order.name)

        res = super(AccountMoveExtend, self).action_post()
        return res





    def write(self, vals):
        is_partner = vals.get('partner_id', False)
        if is_partner and self.is_advance_invoice:
            raise UserError(_('Sorry, you are not allowed to change the customer, for the advance payment invoice'))

        res = super(AccountMoveExtend, self).write(vals)
        return res



    def button_draft(self):
        order = self.sale_order_id
        if self.is_advance_invoice :
            for line in order.order_line:
                if line.qty_delivered > 0:
                    raise UserError(_('Sorry, this Invoice can no longer be reset, due to some delivered order on the sales'))

        if order:
            for picking in order.picking_ids:
                if picking.state != 'cancel':
                    raise UserError(_('Please first of all cancel all delivery orders for the sales order that is attached to this invoice, before this invoice can be reset'))

            if order.state == 'atl_approved' and self.is_advance_invoice :
                raise UserError(_('Sorry, this advance invoice cannot be reset to draft, since the linked sales order is no longer in draft '))
            order.is_has_advance_invoice = True
            order.is_cancelled_invoice = True
            order.is_advance_invoice_validated = False
        res = super(AccountMoveExtend,self).button_draft()
        return res

    def button_cancel(self):
        order = self.sale_order_id
        if self.is_advance_invoice :
            for line in order.order_line:
                if line.qty_delivered > 0:
                    raise UserError(_('Sorry, this Invoice can no longer be cancelled, due to some delivered order on the sales'))

        if order:
            for picking in order.picking_ids:
                if picking.state != 'cancel':
                    raise UserError(_('Please first of all cancel all loading tickets for the sales order that is attached to this invoice, before this invoice can be cancelled'))
            if order.state == 'atl_approved' and self.is_advance_invoice :
                raise UserError(_('Sorry, this advance invoice cannot be reset to draft, since the linked sales order is no longer in draft '))
            order.is_has_advance_invoice = True
            order.is_cancelled_invoice = True
            order.is_advance_invoice_validated = False
        res = super(AccountMoveExtend,self).button_cancel()

        return res

    
    def write(self, vals):
        is_partner = vals.get('partner_id', False)
        if is_partner and self.is_advance_invoice:
            raise UserError(_('Sorry, you are not allowed to change the customer, for the advance payment invoice'))

        res = super(AccountMoveExtend, self).write(vals)
        return res



    throughput_receipt_id = fields.Many2one('kin.throughput.receipt',string="Throughput Receipt")
    is_throughput_invoice = fields.Boolean(string='Throughput Invoice')
    is_has_advance_invoice = fields.Boolean(string="Is Has Advance invoice")
    is_advance_invoice = fields.Boolean(string="Is Advance invoice")
    sales_order_cancel_id = fields.Many2one('sale.order')
    sales_order_transfer_id = fields.Many2one('sale.order')
    is_transfer_invoice = fields.Boolean(string="Is Transfer invoice")
    sales_order_credit_transfer_id = fields.Many2one('sale.order')
    is_from_inventory = fields.Boolean(string='Is From Inventory')
    is_cancelled_remaining_order = fields.Boolean(string='Is Cancelled Remaining Order')
    is_transfer_order = fields.Boolean(string='Is Transfer Order')

    is_truck_park_ticket_invoice = fields.Boolean(string='Truck Park Ticket Invoice')



class AccountMoveLineExtend(models.Model):
    _inherit = 'account.move.line'

    # def write(self, vals):
    #     product_id = vals.get('product_id',False)
    #     account_id = vals.get('account_id',False)
    #     qty = vals.get('quantity',False)
    #     is_product = False
    #     if product_id :
    #         if self.env['product.product'].browse(product_id).type in ('product','consu'):
    #             is_product = True
    #     is_advance_invoice = self.move_id.is_advance_invoice
    #
    #     if is_product and is_advance_invoice :
    #         raise UserError(_('Sorry, you are not allowed to change the advance payment invoice product'))
    #     if account_id and is_advance_invoice :
    #         raise UserError(_('Sorry, you are not allowed to change the account for the advance payment invoice'))
    #     if qty and is_advance_invoice :
    #         raise UserError(_('Sorry, you are not allowed to change the quantity for the advance payment invoice'))
    #
    #     res = super(AccountMoveLineExtend, self).write(vals)
    #     return res


    sales_order_credit_transfer_id = fields.Many2one('sale.order',tracking=True)

class SaleOrderLoading(models.Model):
    _inherit = "sale.order"

    def send_email(self, grp_name, subject, msg):
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref(grp_name)
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)
        if partn_ids:
            # self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))


    def post_customer_credit_transfer_journal_entry(self, journal, from_customer, to_customer, amt, product):

        from_customer_account = from_customer.property_account_receivable_id
        to_customer_account = to_customer.property_account_receivable_id
        mv_lines = []
        move_id = self.env['account.move'].create({
            'journal_id': journal.id,
            'company_id': self.env.user.company_id.id,
            'date': datetime.today(),
            'sales_order_credit_transfer_id': self.id,
        })

        move_line = (0, 0, {
            'name': '%s Transferred Product Qty. for the Order %s' % (product.name, self.name.split('\n')[0][:64]),
            'account_id': from_customer_account.id,
            'partner_id': from_customer.id,
            'debit': amt,
            'credit': 0,
            'ref': self.name,
            'product_id': product.id,
            'sales_order_credit_transfer_id': self.id,
        })
        mv_lines.append(move_line)

        move_line = (0, 0, {
            'name': '%s Transferred Product Qty. for the Order %s' % (product.name, self.name.split('\n')[0][:64]),
            'account_id': to_customer_account.id,
            'partner_id': to_customer.id,
            'debit': 0,
            'credit': amt,
            'ref': self.name,
            'product_id': product.id,
            'sales_order_credit_transfer_id': self.id,
        })
        mv_lines.append(move_line)

        if mv_lines:
            move_id.write({'line_ids': mv_lines})
            move_id.action_post()
        return move_id


    def _prepare_transfer_invoice(self):
        self.ensure_one()
        sale_order = self
        partner_id = self.partner_id
        journal_id = self.env.ref('kin_loading.sales_order_cancel_transfer_journal')
        if not journal_id:
            raise UserError(_('The Sales Order Cancel Transfer Journal is not Present. Please contact the Admin.'))
        partner_invoice_id = partner_id.address_get(['invoice'])['invoice']
        move_type = self._context.get('default_move_type', 'out_refund')
        invoice_vals = {
            'ref': sale_order.client_order_ref or '',
            'move_type': move_type,
            'narration': sale_order.note,
            'currency_id': sale_order.pricelist_id.currency_id.id,
            'invoice_user_id': sale_order.user_id and sale_order.user_id.id,
            'partner_id': partner_id.id,
            'journal_id': journal_id.id,
            'fiscal_position_id': (sale_order.fiscal_position_id or sale_order.fiscal_position_id.get_fiscal_position(
                partner_invoice_id)).id,
            'payment_reference': sale_order.name or '',
            'invoice_origin': sale_order.name,
            'invoice_line_ids': [],
            'company_id': sale_order.company_id.id,
            'user_id': sale_order.user_id and sale_order.user_id.id,
            'team_id': sale_order.team_id.id,
            'invoice_incoterm_id': self.env.company.incoterm_id and self.env.company.incoterm_id.id,
            'is_transfer_invoice': True,
        }
        return invoice_vals



    def _prepare_transfer_account_move_line(self, recipient_id, order_line=False, move=False):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        sale_order_line_id = order_line
        transfer_requested_qty = sale_order_line_id.product_ticket_qty
        qty_bal = sale_order_line_id.product_uom_qty - sale_order_line_id.transfer_created_qty - sale_order_line_id.ticket_created_qty - sale_order_line_id.cancelled_remaining_qty

        if qty_bal == 0:
            raise UserError(_('Sorry, No product Qty to Transfer'))

        if transfer_requested_qty <= 0:
            raise UserError(_('Requested Product Qty. cannot be equal to zero or lesser than zero.'))

        if not float_is_zero(qty_bal, precision_digits=precision):

            if qty_bal == 0:
                raise UserError(_('Sorry, there is no remaining balance qty. to transfer.'))

            if transfer_requested_qty > qty_bal:
                raise UserError(
                    (_('Sorry, you cannot transfer product qty. that is more that the remaining balance qty.')))

            product_deferred_revenue_id = sale_order_line_id.product_id.product_deferred_revenue_id
            if not product_deferred_revenue_id:
                raise UserError(_('Please Define a Deferred Revenue Product for the %s, on the Product Page' % (
                    sale_order_line_id.product_id.name)))

            account = product_deferred_revenue_id.account_unearned_revenue_id
            if not account:
                raise UserError(_(
                    'Please define unearned revenue account for this product: "%s" (id:%d) ') % (
                                    product_deferred_revenue_id.name, product_deferred_revenue_id.id))

            fpos = sale_order_line_id.order_id.fiscal_position_id or sale_order_line_id.order_id.partner_id.property_account_position_id
            if fpos:
                account = fpos.map_account(account)
            ######### OR
            # account = self.env['account.move.line'].get_invoice_line_account('out_invoice', sale_order_line_id.product_id, sale_order_line_id.order_id.fiscal_position_id, self.env.user.company_id)

            default_analytic_account = self.env['account.analytic.default'].sudo().account_get(
                product_id=sale_order_line_id.product_id.id,
                partner_id=sale_order_line_id.order_id.partner_id.id,
                user_id=sale_order_line_id.order_id.user_id.id,
                date=date.today()
            )

            res = {
                'name': 'Transferred product qty. value for %s, from %s to %s' % (
                self.name, sale_order_line_id.order_id.partner_id.name.split('\n')[0][:64], recipient_id.name),
                'display_type': False,
                'product_id': product_deferred_revenue_id.id,
                'product_uom_id': sale_order_line_id.product_uom.id,
                'account_id': account.id,
                'quantity': transfer_requested_qty,
                'discount': sale_order_line_id.discount,
                'price_unit': sale_order_line_id.price_unit,
                'tax_ids': [(6, 0, sale_order_line_id.tax_id.ids)],
                'sale_line_ids': [(6, 0, [sale_order_line_id.id])],
                'analytic_account_id': default_analytic_account and default_analytic_account.analytic_id.id or False,
                'sequence': sale_order_line_id.sequence,
                'ref': sale_order_line_id.order_id.name,
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

    def create_transfer_order(self, recipient_id, sale_order_line_id, transfer_requested_qty):
        # create the transfer sales order
        if not self.root_order_transfer_id:
            tran_root_order_transfer_id = self
        elif self.root_order_transfer_id:
            tran_root_order_transfer_id = self.root_order_transfer_id
        transfer_order_id = self.create({
            'partner_id': recipient_id.id,
            'partner_invoice_id': recipient_id.id,
            'partner_shipping_id': recipient_id.id,
            'pricelist_id': self.pricelist_id.id,
            'client_order_ref': self.name,
            'parent_sales_order_transfer_id': self.id,
            'root_order_transfer_id': tran_root_order_transfer_id.id,
            'order_line': [(0, 0, {
                'name': sale_order_line_id.product_id.name,
                'product_id': sale_order_line_id.product_id.id,
                'discount': sale_order_line_id.discount,
                'product_uom_qty': transfer_requested_qty,
                'product_uom': sale_order_line_id.product_uom.id,
                'price_unit': sale_order_line_id.price_unit,
            })],
        })
        sale_order_line_id.product_ticket_qty = 0
        sale_order_line_id.transfer_created_qty += transfer_requested_qty
        sale_order_line_id.ticket_remaining_qty = sale_order_line_id.product_uom_qty - sale_order_line_id.ticket_created_qty - sale_order_line_id.transfer_created_qty
        transfer_order_id.with_context({'parent_so': self}).action_confirm_main_sale()
        transfer_order_id.is_transferred_order = True
        #sale_order_line_id._compute_procurement_qty()
        return transfer_order_id

    def post_credit_transfer(self, order_line, recipient_id):
        # post credit transfer
        sale_order_line_id = order_line
        transfer_requested_qty = sale_order_line_id.product_ticket_qty
        journal_id = self.env.ref('kin_loading.sales_order_transfer_journal')
        if not journal_id:
            raise UserError(_('The Sales Order Transfer Journal is not Present. Please contact the Admin.'))
        partner_id = self.partner_id or False

        amt = transfer_requested_qty * sale_order_line_id.price_unit
        credit_move_id = self.post_customer_credit_transfer_journal_entry(journal_id, partner_id, recipient_id, amt,
                                                                          sale_order_line_id.product_id)
        transfer_order_id = self.create_transfer_order(recipient_id, sale_order_line_id, transfer_requested_qty)
        return transfer_order_id


    def create_customer_transfer_invoice(self,recipient_id):
        # check if the advance invoice is validated
        for inv in self.invoice_ids:
            if inv.state == 'draft':
                raise UserError(_(
                    "Please contact the accountant to validate the invoice for %s, before cancelling the the order with ID: %s" % (
                        self.partner_id.name, self.name)))

        # 1) Prepare invoice line vals
        invoice_vals_list = []
        invoice_vals = self._prepare_transfer_invoice()
        qty_to_invoice = 0
        qty_to_invoice += sum(self.order_line.mapped('product_ticket_qty'))
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        if not float_is_zero(qty_to_invoice, precision_digits=precision):
            for line in self.order_line:
                invoice_vals['invoice_line_ids'].append((0, 0, self._prepare_transfer_account_move_line(recipient_id,order_line=line)))
                #post credit transfer
                transfer_order_id = self.post_credit_transfer(line,recipient_id)
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(
                _('There is no invoiceable line. The unticketed qty is likely zero. Try to cancel some Unloaded tickets, before you can proceed '))

        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(
            default_move_type='out_refund')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)
            moves.invoice_date = fields.Datetime.now()
            moves.sale_ids = self
            moves.sales_order_transfer_id = self

            # Notify people
            group_name = 'kin_loading.group_notify_transferred_sales'
            msg = _(
                    'A Refund Invoice has been created by %s, for the Sales Order Transfer for customer %s, with Sales ID %s.') % (
                                      self.env.user.name, self.partner_id.name, self.name)
            subject='A Refund Invoice has been created for the Sales Order transfer'
            self.send_email(group_name, subject, msg)

            # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()

        return moves, transfer_order_id






    def create_transfer_sale_order_throughput(self,recipient_id):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        partner_id = self.partner_id or False

        sale_order = self

        for sale_order_line_id in sale_order.order_line :
            transfer_requested_qty = sale_order_line_id.product_ticket_qty
            qty_bal =  sale_order_line_id.product_uom_qty - sale_order_line_id.transfer_created_qty - sale_order_line_id.ticket_created_qty -  sale_order_line_id.cancelled_remaining_qty

            if qty_bal == 0 :
                raise UserError(_('Sorry, No product Qty to Transfer'))

            if transfer_requested_qty <= 0 :
                raise UserError(_('Requested Product Qty. cannot be equal to zero or lesser than zero.'))

            if not float_is_zero(qty_bal, precision_digits=precision):

                if qty_bal == 0 :
                    raise UserError(_('Sorry, there is no remaining balance qty. to transfer.'))

                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                if float_round(transfer_requested_qty,precision_digits) > float_round(qty_bal,precision_digits) :
                    raise UserError((_('Sorry, you cannot transfer product qty. that is more that the remaining balance qty.')))

                #create the transfer sales order
                if not self.root_order_transfer_id :
                    tran_root_order_transfer_id = self
                elif self.root_order_transfer_id :
                    tran_root_order_transfer_id = self.root_order_transfer_id

                transfer_order_id = self.create({
                    'partner_id': recipient_id.id,
                    'partner_invoice_id': recipient_id.id,
                    'partner_shipping_id': recipient_id.id,
                    'pricelist_id': self.pricelist_id.id,
                    'client_order_ref': self.name,
                    'parent_sales_order_transfer_id' :self.id,
                    'root_order_transfer_id': tran_root_order_transfer_id.id,
                    'order_line': [(0, 0, {
                        'name':  sale_order_line_id.product_id.name,
                        'product_id': sale_order_line_id.product_id.id,
                        'discount': sale_order_line_id.discount,
                        'product_uom_qty': transfer_requested_qty,
                        'product_uom': sale_order_line_id.product_uom.id,
                        'price_unit': sale_order_line_id.price_unit,
                    })],
                })
                sale_order_line_id.product_ticket_qty = 0
                sale_order_line_id.transfer_created_qty += transfer_requested_qty
                sale_order_line_id.ticket_remaining_qty = sale_order_line_id.product_uom_qty - sale_order_line_id.ticket_created_qty - sale_order_line_id.transfer_created_qty
                transfer_order_id.is_throughput_order = True
                transfer_order_id.with_context({'parent_so':self}).action_confirm_main_sale()
                transfer_order_id.is_transferred_order = True

                #Create Stock Internal Movement between the througputs
                if not partner_id.throughput_location_id :
                    raise UserError(_('Please ensure there is Throughput Location set for %s', (partner_id.name)))

                if not recipient_id.throughput_location_id:
                    #create new throughput location
                    stock_location = self.env['stock.location']
                    parent_id = self.env['stock.location'].search(
                        [('is_throughput_parent_view', '=', True), ('usage', '=', 'view')], limit=1)
                    if not parent_id:
                        raise UserError(
                            _('Please contact the Administrator to set a parent location for throughput as view type '))
                    vals = {
                        'name': recipient_id.name + ' Throughput Location',
                            'usage': 'internal',
                            'location_id' : parent_id.id,
                            'is_throughput': True,
                    }
                    stock_location_obj = stock_location.create(vals)
                    recipient_id.throughput_location_id = stock_location_obj


                stock_move_obj = self.env['stock.move']
                #self.product_id.standard_price = 0
                vals = {
                    'name': self.name,
                    'product_id': sale_order_line_id.product_id.id,
                    'product_uom': sale_order_line_id.product_uom.id,
                    #'price_unit': 0,
                    'date': datetime.today().strftime('%Y-%m-%d'),
                    'location_id': partner_id.throughput_location_id.id,
                    'location_dest_id': recipient_id.throughput_location_id.id,
                    'product_uom_qty': transfer_requested_qty,
                    'origin': self.name
                }

                move_id = stock_move_obj.create(vals)
                move_id.action_confirm()
                move_id.force_assign()
                move_id.action_done()
                move_id.throughput_so_transfer_movement_id = self.id

        # send notification
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref('kin_loading.group_notify_transferred_sales')
        msg = 'The Throughput Transfer Order (%s) for (%s), has been created by %s' % (
            transfer_order_id.name, transfer_order_id.partner_id.name, self.env.user.name)
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_post(
                _(msg),
                subject='%s' % msg, partner_ids=partn_ids)
        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        return transfer_order_id




    def create_transfer_sale_order(self):
        recipient_id = self.env.context.get('recipient_id', False)

        if recipient_id == self.partner_id :
            raise UserError('Sorry, you cannot transfer from %s to %s' % (self.partner_id.name, recipient_id.name))

        if self.is_internal_use_order :
            raise UserError(_('Sorry, No transfer for Internal Use operations'))
        if not recipient_id:
            raise UserError(_('Sorry, no recipient for this transfer order. Please contact the admin'))

        if self.is_throughput_order :
            self.create_transfer_sale_order_throughput(recipient_id)

        if not self.is_throughput_order :
            parent_tran_inv, transfer_order_id = self.create_customer_transfer_invoice(recipient_id)
            parent_tran_inv.action_post()
            for invoice in transfer_order_id.invoice_ids :
                invoice.action_post()
                invoice.is_transfer_invoice = True
            transfer_order_id.atl_depot_id = self.atl_depot_id
            transfer_order_id.atl_payment_mode_id = self.atl_payment_mode_id
            transfer_order_id.atl_jetty_id = self.atl_jetty_id
            transfer_order_id.action_atl_approval()
            #res = transfer_order_id.action_view_transfers()  #TODO this is not working. Check later

        self.env.user.notify_info('TRANSFER ORDER HAS BEEN CREATED.')


    def btn_view_refund_invoice(self):
        invoice_ref_ids = self.mapped('invoice_ref_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")

        if len(invoice_ref_ids) > 1:
            action['domain'] = [('id', 'in', invoice_ref_ids.ids)]
        elif len(invoice_ref_ids) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoice_ref_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        #action['target'] = 'new'

        context = {
            #'default_move_type': 'out_invoice',
        }
        # if len(self) == 1:
        #     context.update({
        #         'default_partner_id': self.partner_id.id,
        #         'default_partner_shipping_id': self.partner_shipping_id.id,
        #         'default_invoice_payment_term_id': self.payment_term_id.id or self.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
        #         'default_invoice_origin': self.mapped('name'),
        #         'default_user_id': self.user_id.id,
        #     })
        action['context'] = context
        return action




    @api.depends('invoice_ref_ids')
    def _compute_ref_count(self):
        for rec in self:
            rec.ref_count = len(rec.invoice_ref_ids)



    def btn_view_transfer_invoice(self):
        invoice_tran_ids = self.mapped('invoice_tran_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_refund_type")

        if len(invoice_tran_ids) > 1:
            action['domain'] = [('id', 'in', invoice_tran_ids.ids)]
        elif len(invoice_tran_ids) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoice_tran_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        # action['target'] = 'new'

        context = {
            # 'default_move_type': 'out_invoice',
        }
        # if len(self) == 1:
        #     context.update({
        #         'default_partner_id': self.partner_id.id,
        #         'default_partner_shipping_id': self.partner_shipping_id.id,
        #         'default_invoice_payment_term_id': self.payment_term_id.id or self.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
        #         'default_invoice_origin': self.mapped('name'),
        #         'default_user_id': self.user_id.id,
        #     })
        action['context'] = context
        return action



    @api.depends('invoice_tran_ids')
    def _compute_tran_count(self):
        for rec in self:
            rec.tran_count = len(rec.invoice_tran_ids)


    def btn_view_child_sales_orders(self):
        child_sale_order_transfer_ids = self.mapped('child_sale_order_transfer_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")

        if len(child_sale_order_transfer_ids) > 1:
            action['domain'] = [('id', 'in', child_sale_order_transfer_ids.ids)]
        elif len(child_sale_order_transfer_ids) == 1:
            form_view = [(self.env.ref('sale.view_order_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = child_sale_order_transfer_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        #action['target'] = 'new'

        context = {
            #'default_move_type': 'out_invoice',
        }
        # if len(self) == 1:
        #     context.update({
        #         'default_partner_id': self.partner_id.id,
        #         'default_partner_shipping_id': self.partner_shipping_id.id,
        #         'default_invoice_payment_term_id': self.payment_term_id.id or self.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
        #         'default_invoice_origin': self.mapped('name'),
        #         'default_user_id': self.user_id.id,
        #     })
        action['context'] = context
        return action

    @api.depends('child_sale_order_transfer_ids')
    def _compute_cso_count(self):
        for rec in self:
            rec.cso_count = len(rec.child_sale_order_transfer_ids)


    
    def btn_view_jnr(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.move_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('move_ids')
    def _compute_jnr_count(self):
        for rec in self:
            rec.jnr_count = len(rec.move_ids)


    
    def action_transfer_wizard(self):

        model_data_obj = self.env['ir.model.data']
        action = self.env['ir.model.data'].xmlid_to_object('kin_loading.action_transfer_order_wizard')
        form_view_id = model_data_obj.xmlid_to_res_id('kin_loading.view_transfer_order_wizard')

        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'context': {'the_order_id':self.id},
            'res_model': action.res_model,
        }


    def action_view_transfers(self):
        model_data_obj = self.env['ir.model.data']
        action = self.env['ir.model.data'].xmlid_to_object('sale.action_orders')
        form_view_id = model_data_obj.xmlid_to_res_id('sale.view_order_form')

        res = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': 'new',
            'context': {'show_sale': True},
            'res_model': action.res_model,
        }
        return res




    
    def action_create_transfer_order(self):
        for order in self:

            if order.is_cancelled_order:
                raise UserError(_('You cannot create new transfer order for the cancelled order'))

            if order.state == 'done':
                raise UserError(_('The Sales is already done. Nothing more to do'))

            if len(order.invoice_ids) == 0 and not order.is_throughput_order and not order.is_internal_use_order:
                raise UserError(_('No Advance Payment Invoice. Please Contact the Admin'))

            if not order.is_has_advance_invoice and not order.is_throughput_order and not order.is_internal_use_order :
                raise UserError(_('No Advance Payment Invoice. Please Contact the Admin'))

            if  order.is_cancelled_invoice :
                raise UserError(_('Advance Payment Invoice for this Sales Order has been Cancelled. Please contact the admin'))

            if not order.is_advance_invoice_validated and not order.is_throughput_order and not order.is_internal_use_order:
                raise UserError(_(
                    "Please contact the accountant to validate the invoice before creating a transfer order for the sales order: %s, belonging to %s" % (
                    order.name,order.partner_id.name)))

            res =  order.create_transfer_sale_order()
            return res


    
    def action_ticket_wizard(self):

        for inv in self.invoice_ids:
            if inv.state == 'draft':
                raise UserError(_(
                    "Please contact the accountant to validate the invoice for %s, before creating loading tickets for the order with ID: %s" % (
                        self.partner_id.name, self.name)))

        model_data_obj = self.env['ir.model.data']
        action = self.env['ir.model.data'].ref('kin_loading.action_loading_ticket_wizard')
        form_view_id = model_data_obj.ref('kin_loading.view_loading_ticket_wizard')

        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'context': {'the_order_id':self.id},
            'res_model': action.res_model,
        }



    
    def action_view_delivery(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = form = False
        if self.is_throughput_order :
            action = self.env.ref('kin_loading.action_throughput_dispatch')
            form = self.env.ref('kin_loading.view_picking_throughput_form', False)
        elif self.is_internal_use_order:
            action = self.env.ref('kin_loading.action_internal_use_dispatch')
            form = self.env.ref('kin_loading.view_picking_internal_use_form', False)
        else:
            action = self.env.ref('kin_loading.action_depot_dispatch')
            form = self.env.ref('kin_loading.view_picking_depot_form', False)

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': 'tree',
            'views': [(self.env.ref('kin_loading.vpicktree_depot').id, 'tree'),
                      (self.env.ref('kin_loading.view_picking_depot_form').id, 'form')],
            'view_id': self.env.ref('kin_loading.vpicktree_depot').id,
            'context': action.context,
            'res_model': action.res_model,
        }
        pick_ids = sum([order.picking_ids.ids for order in self], [])
        if len(pick_ids) > 0:
            result['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        # elif len(pick_ids) == 1:
        #     form_id = form.id if form else False
        #     result['views'] = [(form_id, 'form')]
        #     result['res_id'] = pick_ids[0]
        return result

    
    def action_create_loading_ticket(self):
        for order in self:
            if order.is_cancelled_order:
                raise UserError(_('You cannot create loading Ticket for cancelled order'))

            if order.state == 'done':
                raise UserError(_('The Sales is already done. Nothing more to do'))

            if len(order.invoice_ids) == 0 and not order.is_throughput_order and not order.is_internal_use_order:
                raise UserError(_('No Advance Payment Invoice. Please Contact the Admin'))

            if not order.is_has_advance_invoice and not order.is_throughput_order and not order.is_internal_use_order:
                raise UserError(_('No Advance Payment Invoice. Please Contact the Admin'))

            if  order.is_cancelled_invoice :
                raise UserError(_('Advance Payment Invoice for this Sales Order has been Cancelled. Please contact the admin'))

            if not order.is_advance_invoice_validated and not order.is_throughput_order and not order.is_internal_use_order :
                raise UserError(_(
                    "Please contact the accountant to validate the invoice before creating a loading ticket for the sales order: %s, belonging to %s" % (
                    order.name,order.partner_id.name)))

            res =  order.order_line._action_launch_stock_rule()

        return res


    def _prepare_refund_invoice(self):
        self.ensure_one()
        sale_order = self
        partner_id = self.partner_id
        journal_id = self.env.ref('kin_loading.sales_order_cancel_transfer_journal')
        if not journal_id:
            raise UserError(_('The Sales Order Cancel Transfer Journal is not Present. Please contact the Admin.'))

        partner_invoice_id = partner_id.address_get(['invoice'])['invoice']
        move_type = self._context.get('default_move_type','out_refund')
        invoice_vals = {
            'ref': sale_order.client_order_ref or '',
            'move_type': move_type,
            'narration': sale_order.note,
            'currency_id': sale_order.pricelist_id.currency_id.id,
            'invoice_user_id': sale_order.user_id and sale_order.user_id.id,
            'partner_id': partner_id.id,
            'journal_id': journal_id.id,
            'fiscal_position_id': (sale_order.fiscal_position_id or sale_order.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
            # 'fiscal_position_id': sale_order.fiscal_position_id.id or sale_order.partner_invoice_id.property_account_position_id.id,
            'payment_reference': sale_order.name or '',
            'invoice_origin': sale_order.name ,
            'invoice_line_ids': [],
            'company_id': sale_order.company_id.id,
            'user_id': sale_order.user_id and sale_order.user_id.id,
            'team_id': sale_order.team_id.id,
            'invoice_incoterm_id': self.env.company.incoterm_id and self.env.company.incoterm_id.id,
            'is_cancelled_remaining_order': True,
        }
        return invoice_vals



    def _prepare_account_move_line(self, order_line=False, move=False):
        self.ensure_one()
        sale_order_line_id = order_line
        product_deferred_revenue_id = sale_order_line_id.product_id.product_deferred_revenue_id
        if not product_deferred_revenue_id:
            raise UserError(_('Please Define a Deferred Revenue Product for the %s, on the Product Page' % (
                sale_order_line_id.product_id.name)))

        account = product_deferred_revenue_id.account_unearned_revenue_id
        if not account:
            raise UserError(_(
                'Please define unearned revenue account for this product: "%s" (id:%d)') % (
                                product_deferred_revenue_id.name, product_deferred_revenue_id.id))

        fpos = sale_order_line_id.order_id.fiscal_position_id or sale_order_line_id.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        default_analytic_account = self.env['account.analytic.default'].sudo().account_get(
            product_id = sale_order_line_id.product_id.id,
            partner_id = sale_order_line_id.order_id.partner_id.id,
            user_id = sale_order_line_id.order_id.user_id.id,
            date = datetime.today()
        )

        qty_bal = sale_order_line_id.ticket_remaining_qty
        if qty_bal == 0:
            raise UserError(_('Sorry, there is no remaining balance to cancel.'))
        if qty_bal < 0:
            raise UserError(_('Sorry, Qty Bal (%s) is < 0. Please contact your admin.' % (qty_bal)))

        res = {
            'display_type': False,
            'sequence': 10,
            'name': 'Cancelled Order for %s' % self.name.split('\n')[0][:64],
            'product_id': product_deferred_revenue_id.id,
            'product_uom_id': sale_order_line_id.product_uom.id,
            'quantity': qty_bal,
            'price_unit': sale_order_line_id.price_unit,
            'tax_ids': [(6, 0, sale_order_line_id.tax_id.ids)],
            'discount': sale_order_line_id.discount,
            'sale_line_ids': [(6, 0, [sale_order_line_id.id])],
            'analytic_account_id': default_analytic_account and default_analytic_account.analytic_id.id,
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


    #For refunding the remaining cancelled order value to the customers account
    def create_customer_refund_invoice(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}

        journal_id = self.env.ref('kin_loading.sales_order_cancel_transfer_journal')
        if not journal_id:
            raise UserError(_('The Sales Order Cancel Transfer is not Present. Please contact the Admin.'))

        partner_id = self.partner_id or False

        # check if the advance invoice is validated
        for inv in self.invoice_ids:
            if inv.state == 'draft':
                raise UserError(_(
                    "Please contact the accountant to validate the invoice for %s, before cancelling the the order with ID: %s" % (
                        self.partner_id.name, self.name)))

        total_can_bal = 0
        total_tik_rem = 0
        unloaded_balance_qty = 0

        # 1) Prepare invoice line vals
        invoice_vals_list = []
        invoice_vals = self._prepare_refund_invoice()
        qty_to_invoice = 0
        qty_to_invoice += sum(self.order_line.mapped('ticket_remaining_qty'))
        if not float_is_zero(qty_to_invoice, precision_digits=precision):
            for line in self.order_line:
                invoice_vals['invoice_line_ids'].append((0, 0, self._prepare_account_move_line(order_line=line)))

                #update the order line
                qty_bal = line.ticket_remaining_qty
                line.cancelled_remaining_qty += qty_bal
                line.ticket_remaining_qty = line.product_uom_qty - line.ticket_created_qty - line.transfer_created_qty - line.cancelled_remaining_qty
                total_can_bal += line.cancelled_remaining_qty
                total_tik_rem += line.ticket_remaining_qty
                line.product_ticket_qty = 0
                unloaded_balance_qty = line.unloaded_balance_qty

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(
                _('There is no invoiceable line. The unticketed qty is likely zero. Try to cancel some Unloaded tickets, before you can proceed '))

        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(
            default_move_type='out_refund')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)
            moves.invoice_date = fields.Datetime.now()
            moves.action_post()
            moves.sale_ids = self
            moves.sales_order_cancel_id = self
            if total_can_bal > 0 and total_tik_rem == 0 and unloaded_balance_qty == 0:
                self.is_cancelled_order = True
                self.action_done()

            # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(lambda m: m.currency_id.round(m.amount_total)
                       < 0).action_switch_invoice_into_refund_credit_note()

        # Notify people
        group_name = 'kin_loading.group_notify_cancelled_sales'
        msg = _('A Sales Order Remaining Qty. from %s has been Cancelled and a Refund Invoice has been created for the customer %s, with Sales ID %s.') % (
                                  self.env.user.name, self.partner_id.name, self.name)
        subject='A Sales Order Remaining order qty has been cancelled with a corresponding refund invoice'
        self.send_email(group_name, subject, msg)

        return moves



    # 
    # def post_deferred_revenue_transfer_journal_entry(self):
    #     journal_id = self.env.ref('kin_loading.sales_order_cancel_transfer_journal')
    #     company = self.env.user.company_id
    #
    #     partner_id = self.partner_id or False
    #     precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #
    #
    #     # check if the advance invoice is validated
    #     for inv in self.invoice_ids:
    #         if inv.state == 'draft':
    #             raise UserError(_(
    #                 "Please contact the accountant to validate the invoice for %s, before cancelling the the order with ID: %s" % (
    #                 self.partner_id.name, self.name)))
    #
    #
    #     if not journal_id:
    #         raise UserError(_('The Sales Order Cancel Transfer is not Present. Please contact the Admin.'))
    #
    #     mv_lines = []
    #     ctx = dict(self._context)
    #     ctx['is_ssd_sbu'] = self.is_ssd_sbu
    #     ctx['hr_department_id'] = self.hr_department_id
    #     ctx['sbu_id'] = self.sbu_id
    #     ctx['is_ssa_allow_split'] = True
    #
    #     move_id = self.env['account.move'].with_context(ctx).create({
    #             'journal_id': journal_id.id,
    #             'company_id': self.env.user.company_id.id,
    #             'date': datetime.today(),
    #             'sales_order_cancel_id': self.id,
    #             'partner_id' : partner_id.id,
    #         })
    #     partner_account = self.partner_id.property_account_receivable_id
    #
    #     for sale_order_line_id in self.order_line :
    #         qty_bal = sale_order_line_id.ticket_created_qty - sale_order_line_id.transfer_created_qty - sale_order_line_id.qty_delivered
    #         if not float_is_zero(qty_bal, precision_digits=precision):
    #             qty_bal = sale_order_line_id.product_uom_qty - sale_order_line_id.qty_delivered - sale_order_line_id.transfer_created_qty
    #             if not float_is_zero(qty_bal, precision_digits=precision):
    #                 if qty_bal == 0 :
    #                         raise UserError(_('Sorry, there is no remaining balance to cancel.'))

    #             account = sale_order_line_id.product_id.account_unearned_revenue_id
    #             if not account:
    #                 raise UserError(_(
    #                     'Please define unearned revenue account for this product: "%s" (id:%d)') % (
    #                                 sale_order_line_id.product_id.name, sale_order_line_id.product_id.ide))
    #
    #             fpos = sale_order_line_id.order_id.fiscal_position_id or sale_order_line_id.order_id.partner_id.property_account_position_id
    #             if fpos:
    #                 account = fpos.map_account(account)
    #             account = sale_order_line_id.product_id.account_unearned_revenue_id
    #             default_analytic_account = self.env['account.analytic.default'].account_get(
    #                 sale_order_line_id.product_id.id, sale_order_line_id.order_id.partner_id.id,
    #                 sale_order_line_id.order_id.user_id.id, date.today())
    #
    #             move_line = (0, 0, {
    #                     'name': 'Cancelled Order for %s' % self.name.split('\n')[0][:64],
    #                     'account_id': account.id,
    #                     'partner_id': partner_id.id,
    #                     'debit': sale_order_line_id.ticket_remaining_qty * sale_order_line_id.price_unit,
    #                     'credit': 0,
    #                     'ref': self.name,
    #                     'product_id' : sale_order_line_id.product_id.id,
    #                     'sales_order_cancel_id': self.id,
    #             })
    #             mv_lines.append(move_line)
    #
    #             move_line = (0, 0, {
    #                     'name': 'Cancelled Order for %s' % self.name.split('\n')[0][:64],
    #                     'account_id': partner_account.id,
    #                     'partner_id': partner_id.id,
    #                     'debit': 0,
    #                     'credit': sale_order_line_id.ticket_remaining_qty * sale_order_line_id.price_unit,
    #                     'ref': self.name,
    #                     'product_id': sale_order_line_id.product_id.id,
    #                     'sales_order_cancel_id': self.id,
    #             })
    #             mv_lines.append(move_line)
    #
    #     if mv_lines:
    #         move_id.write({'line_ids': mv_lines})
    #         move_id.action_post()
    #         self.is_cancelled_order = True
    #
    #         # Notify people
    #         user_ids = []
    #         group_obj = self.env.ref('kin_loading.group_notify_cancelled_sales')
    #         for user in group_obj.users:
    #             user_ids.append(user.id)
    #
    #             self.message_unsubscribe_users(user_ids=user_ids)
    #             self.message_subscribe_users(user_ids=user_ids)
    #             self.message_post(_(
    #                 'A Sales Order Remaining Qty. from %s has been Cancelled and Deferred Revenue account move has been effected for the customer %s, with Sales ID %s.') % (
    #                                   self.env.user.name, self.partner_id.name, self.name),
    #                               subject='A Sales Order Remaining has been Cancelled with effect on Accounting ', subtype_xmlid='mail.mt_comment', force_send=False)
    #
    #     return


    
    def action_cancel_balance_order(self,is_cancel_unloaded_unticketed_qty):
        if self.is_throughput_order :
            raise UserError(_('Sorry, No Cancelation for Throughput Order'))
        if self.is_cancelled_order :
            raise UserError(_('The order has been cancelled already'))
        if self.state == 'done':
            raise UserError(_('The Sales is already done. Nothing more to do'))
        if self.is_cancelled_invoice:
            raise UserError(
                _('Advance Payment Invoice for this Sales Order has been Cancelled. Please contact the admin'))

        to_cancel_tickets = ''
        if is_cancel_unloaded_unticketed_qty == 'unloaded_cancel' :
            for picking in self.picking_ids:
                if picking.state not in  ['cancel','done']:
                    to_cancel_tickets += picking.name + '\n'
            if to_cancel_tickets :
                raise UserError(_(
                        'Kindly cancel the loading Ticket(s) with the following ID(s), before you can cancel the sales order: %s' % (to_cancel_tickets)))
        elif is_cancel_unloaded_unticketed_qty == 'select_one' :
            raise UserError(_('Please Select one of the Cancellation Type Below'))
        inv = self.create_customer_refund_invoice()

        return


    
    def action_ticket_wizard(self):

        for inv in self.invoice_ids:
            if inv.state == 'draft':
                raise UserError(_(
                    "Please contact the accountant to validate the invoice for %s, before creating loading tickets for the order with ID: %s" % (
                        self.partner_id.name, self.name)))

        model_data_obj = self.env['ir.model.data']
        action = self.env['ir.model.data'].xmlid_to_object('kin_loading.action_loading_ticket_wizard')
        form_view_id = model_data_obj.xmlid_to_res_id('kin_loading.view_loading_ticket_wizard')

        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'context': {'the_order_id':self.id},
            'res_model': action.res_model,
        }

    def _get_invoiceable_lines(self, final=False):
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


    def _create_advance_invoice_depot(self,grouped=False, final=False):

        # 1) Create invoices.
        invoice_vals_list = []
        invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
        for order in self:
            order = order.with_company(order.company_id)
            current_section_vals = None
            down_payments = order.env['sale.order.line']

            invoice_vals = order._prepare_invoice()
            invoiceable_lines = order._get_invoiceable_lines(final=final)

            if not any(not line.display_type for line in invoiceable_lines):
                raise self._nothing_to_invoice_error()

            invoice_line_vals = []
            down_payment_section_added = False
            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    # Create a dedicated section for the down payments
                    # (put at the end of the invoiceable_lines)
                    invoice_line_vals.append(
                        (0, 0, order._prepare_down_payment_section_line(
                            sequence=invoice_item_sequence,
                        )),
                    )
                    dp_section = True
                    invoice_item_sequence += 1
                invoice_line_vals.append(
                    (0, 0, line._prepare_invoice_line(
                        sequence=invoice_item_sequence,
                    )),
                )
                invoice_item_sequence += 1

            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise self._nothing_to_invoice_error()

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.

        # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
        # in a single invoice. Example:
        # SO 1:
        # - Section A (sequence: 10)
        # - Product A (sequence: 11)
        # SO 2:
        # - Section B (sequence: 10)
        # - Product B (sequence: 11)
        #
        # If SO 1 & 2 are grouped in the same invoice, the result will be:
        # - Section A (sequence: 10)
        # - Section B (sequence: 10)
        # - Product A (sequence: 11)
        # - Product B (sequence: 11)
        #
        # Resequencing should be safe, however we resequence only if there are less invoices than
        # orders, meaning a grouping might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['sale.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                subtype_id=self.env.ref('mail.mt_note').id
            )
        return moves


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
        if is_post_invoice_before_delivery:
            inv.action_post()
        return inv


    def action_submit_to_manager(self):
        self.state = 'so_to_approve'
        # Send Email to sales manager
        grp_name = 'kin_loading.group_show_confirm_main_sale'
        subject = 'A New Sales Quote has been Submitted'
        msg = _('A New Sales Quote has been submitted by %s for the customer (%s)') % (
                                     self.env.user.name, self.partner_id.name)
        self.send_email(grp_name,subject, msg)


    def action_atl_approval(self):
        if not self.atl_depot_id:
            raise UserError('Kindly fill in the depot field in the Authority to Load tab below')
        if not self.atl_jetty_id:
            raise UserError('Kindly fill in the jetty field in the Authority to Load tab below ')
        #check if advance invoice has not been deleted
        if not self.advance_invoice_id :
            raise UserError('Sorry, you have to cancel this document and start afresh. The advance invoice linked to this order has been deleted. So you cannot approve an ATL without an advance invoice')
        # check if the advance invoice is validated
        for inv in self.invoice_ids:
            if inv.state != 'posted':
                raise UserError(_(
                    "Kindly contact the accountant to post the invoice for %s, before this order (%s) can be authorized to load" % (
                        self.partner_id.name, self.name)))

        self.state = 'atl_approved'
        self.atl_id = self.env['ir.sequence'].next_by_code('atl_code')
        self.atl_approved_user_id = self.env.user
        self.atl_date = datetime.today()
        self.is_has_advance_invoice = True
        self.is_cancelled_invoice = False
        self.is_advance_invoice_validated = True
        user_name = self.env.user.name
        #send email to user/dispatch officer, notifying them to create loading tickets
        self.send_email(grp_name='kin_loading.group_receive_atl_approved',
                        subject='The ATL document (ATL_ID_HERE_PLEASE) has been approved by %s, you may now create loading tickets' % (user_name),
                        msg='The ATL document (ATL_ID_HERE_PLEASE) for the sales order (%s) has been approved by %s, you may now create loading tickets' % (self.name,user_name))

    def action_confirm_main_sale(self):
        list_data = []
        is_contraint_sales_order_stock = self.env['ir.config_parameter'].sudo().get_param('is_contraint_sales_order_stock', default=False)
        is_sales_order_stock_notification = self.env['ir.config_parameter'].sudo().get_param('is_sales_order_stock_notification', default=False)
        is_sales_order_stock_count_error = self.env['ir.config_parameter'].sudo().get_param('is_sales_order_stock_count_error', default=False)
        is_sales_order_stock_purchase_request = self.env['ir.config_parameter'].sudo().get_param('is_sales_order_stock_purchase_request', default=False)
        is_po_check = self.env['ir.config_parameter'].sudo().get_param('is_po_check', default=False)

        customer = self.partner_id

        #check the number of lines
        if len(self.order_line) > 1 :
            raise UserError(_('Only one product can be ordered at a time'))

        # is PO Check
        if is_po_check:
            if self.client_order_ref:
                client_order_ref = self.client_order_ref.strip()

                if len(client_order_ref) <= 0:
                    raise UserError(
                        'Please Ensure that the Quote is confirmed from the customer and that the PO reference is set. e.g. you may put the po number, email, contact name, number of the customer that confirmed the Quote on the PO reference field')

            else:
                raise UserError(
                    'Please Ensure that the Quote is confirmed from the customer and that the PO reference is set. e.g. you may put the po number, email, contact name, number of the customer that confirmed the Quote')

        #Credit limit Check
        if customer.is_enforce_credit_limit_so:
            if self.amount_total > customer.allowed_credit :
                raise UserError('Total Amount %s%s has exceeded the remaining credit %s%s for %s' % (
                self.currency_id.symbol, self.amount_total, self.currency_id.symbol, customer.allowed_credit,
                customer.name))

        #Low stock check
        msg, stock_locations = self.get_low_stock_msg()
        if msg and is_contraint_sales_order_stock and is_sales_order_stock_notification :
            # Check product qty if is less than 0 for each location
            sale_stock_loc_ids = self.team_id.sale_stock_location_ids

            # Create Purchase Request with email notification for low stock
            if is_sales_order_stock_purchase_request:
                pr_id = self.create_purchase_request(sale_stock_loc_ids)
                self.send_email(grp_name='kin_sales.group_receive_sale_order_purchase_request_email',
                                subject='Purchase Request from Sales Order (%s)' % self.name,
                                msg='A new purchase request document for the sales order (%s) has been created.' % self.name)

            if is_sales_order_stock_notification:
                self.send_email(grp_name='kin_sales.group_receive_sale_order_stock_alert_email',
                                subject='Stock Alert Message from Sales Order (%s) ' % self.name,
                                msg='The Items listed from the (%s), are below the quantities that are to be sold for the sales order (%s).' % (
                                stock_locations, self.name))

        if msg and is_sales_order_stock_count_error :
            raise UserError(_(msg))

        # Send Email to the Stock Person
        # self.send_email(grp_name='kin_sales.group_receive_delivery_stock_transfer_email',
        #                     subject='A New Delivery transfer document for the sales order (%s) has been created.' % self.name,
        #                     msg='A New Delivery transfer document for the sales order (%s) has been created.' % self.name)
        #


        self.create_advance_invoice_depot()
        # Send Email to the Accountant
        self.send_email(grp_name='kin_sales.group_invoice_before_delivery_email',
                            subject='A New draft advance invoice with source document (%s) has been created for the customer (%s)' % (self.name,self.partner_id.name),
                            msg='A New Draft Invoice with Source Document Number (%s) has been created. Crosscheck and validate the invoice'  % self.name)


        #For throughput or internal use orders
        # if not self.is_throughput_order and not self.is_internal_use_order :
        #     self.create_advance_invoice()

        return True




    
    def unlink(self):
        for rec in self:
            if rec.is_throughput_order:
                raise UserError(_('Sorry, Throughput Order cannot be deleted'))

        return super(SaleOrderLoading, self).unlink()


    
    def action_cancel(self):
        res = super(SaleOrderLoading,self).action_cancel()
        self.advance_invoice_id.unlink()
        self.is_has_advance_invoice = False
        self.is_cancelled_invoice = True
        self.is_advance_invoice_validated = False

        if self.is_throughput_order :
            raise UserError(_('Sorry, Transfer is not allowed for Throughput Order'))

        #Send Email
        company_email = self.env.user.company_id.email.strip()
        sales_person_email = self.user_id.partner_id.email.strip()
        confirm_person_email = self.env.user.partner_id.email.strip()

        if company_email and sales_person_email and confirm_person_email and  (sales_person_email != confirm_person_email ):
            # Custom Email Template
            mail_template = self.env.ref('kin_loading.mail_templ_sale_canceled')
            ctx = {}
            ctx.update({'sale_id':self.id})
            the_url = self._get_sale_order_url('sale','menu_sale_order','action_orders',ctx)

            ctx = {'system_email': company_email,
                    'confirm_person_name': self.env.user.name ,
                    'confirm_person_email' :confirm_person_email,
                    'url':the_url
                    }
            mail_template.with_context(ctx).send_mail(self.id,force_send=False)
        return res


    
    def action_disapprove(self, msg):
        reason_for_dispproval = msg
        self.disapproved_by_user_id = self.env.user
        self.state = 'no_sale'

        # Send email to sales person
        partn_ids = []
        user = self.user_id
        user_name = user.name
        partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_follower_ids.unlink()
            msg = _("Sales Order has been Disapproved with reason: %s" % (reason_for_dispproval))
            subject = 'Sales Order (%s) has been Disapproved for %s' % (self.name, self.atl_partner_id.name) ,
            self.message_post(
                body=msg,
                subject=subject, partner_ids=partn_ids,
                subtype_xmlid='mail.mt_comment', force_send=False)

        #send email to group
        group_name = 'kin_loading.group_receive_disapprove_sale_order_email'
        self.send_email(group_name, subject, msg)


    def action_reset(self):
        self.action_cancel()
        self.state = 'draft'


    def btn_view_stock_moves(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_move_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_move_ids')
    def _compute_stock_move_count(self):
        for rec in self:
            rec.stock_move_count = len(rec.stock_move_ids)

    @api.depends('order_line')
    def _compute_atl_fields(self):
        for rec in self:
            line = rec.order_line and rec.order_line[0]
            rec.atl_product_id = line.product_id or False
            rec.atl_qty = line.product_uom_qty or False


    authorization_code = fields.Char(string='Authorization Code',readonly=True)
    is_has_advance_invoice = fields.Boolean(string="Has Advance invoice")
    is_advance_invoice_validated = fields.Boolean(string="Advance Invoice Validated")
    is_cancelled_invoice = fields.Boolean(string="Is Cancelled Advance Invoice")
    is_cancelled_order = fields.Boolean(string="Is Cancelled Order")
    is_transferred_order = fields.Boolean(string="Is Transferred Order")
    jnr_count = fields.Integer(compute="_compute_jnr_count", string='# of Journal Items', copy=False, default=0)
    move_ids = fields.One2many('account.move', 'sales_order_credit_transfer_id', string='Journal Entry')
    ref_count = fields.Integer(compute="_compute_ref_count", string='# of Refund Invoice', copy=False, default=0)
    invoice_ref_ids = fields.One2many('account.move', 'sales_order_cancel_id', string='Refund Invoices')
    tran_count = fields.Integer(compute="_compute_tran_count", string='# of Transfer Invoice', copy=False, default=0)
    invoice_tran_ids = fields.One2many('account.move', 'sales_order_transfer_id', string='Transfer Invoices')
    parent_sales_order_transfer_id = fields.Many2one('sale.order',string="Parent Sales Order Transfer")
    cso_count = fields.Integer(compute="_compute_cso_count", string='# of Child Sale Orders', copy=False, default=0)
    child_sale_order_transfer_ids = fields.One2many('sale.order', 'parent_sales_order_transfer_id', string='Parent Sales Orders')
    root_order_transfer_id = fields.Many2one('sale.order',string='Root Transfer Sales Order')
    root_customer_id = fields.Many2one('res.partner', related='root_order_transfer_id.partner_id', store=True,
                                       string='Root Transfer Customer Name')
    advance_invoice_id = fields.Many2one('account.move',string="Advance Invoice")
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('so_to_approve', 'Sale Order To Approve'),
        ('sale', 'Sale Order Approved'),
        ('no_sale', 'Sale Order Disapproved'),
        ('atl_awaiting_approval', 'ATL Awaiting Approval'),
        ('atl_approved', 'ATL Approved'),
        ('credit_limit_by_pass_request', 'Credit Limit By Pass Request'),
        ('credit_limit_by_pass_confirm', 'Credit Limit By Pass Confirmed'),
        ('credit_limit_by_pass_approve', 'Credit Limit By Pass Approved'),
        ('credit_limit_by_pass_disapprove', 'Credit Limit By Pass DisApproved'),
        ('credit_limit_by_pass_cancel', 'Credit Limit By Pass Cancelled'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')
    confirmed_by_user_id = fields.Many2one('res.users', string='Confirmed By')
    approved_by_user_id = fields.Many2one('res.users', string='Approved By')
    disapproved_by_user_id = fields.Many2one('res.users', string='Disapproved By')
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
                                 states={'draft': [('readonly', False), ('required', False)],
                                         'sent': [('readonly', False)], 'waiting': [('readonly', False)],
                                         'so_to_approve': [('readonly', False)]}, copy=False)
    is_throughput_order = fields.Boolean(string='Is throughput Order')
    throughput_receipt_source_id = fields.Many2one('kin.throughput.receipt', string="Throughput Receipt Order Source")
    is_internal_use_order = fields.Boolean(string='Is Internal Use Order')
    internal_use_source_id = fields.Many2one('kin.internal.use', string="Internal Use Order Source")
    stock_move_count = fields.Integer(compute="_compute_stock_move_count", string='# of Throughput Stock Moves', copy=False,
                                      default=0)
    stock_move_ids = fields.One2many('stock.move', 'throughput_so_transfer_movement_id', string='Throughput Stock Moves Entry(s)')

    atl_partner_id = fields.Many2one('res.partner', related='partner_id', string='ATL Name')
    atl_product_id = fields.Many2one('product.product', compute="_compute_atl_fields", string='Product')
    atl_qty = fields.Float(compute="_compute_atl_fields", string='ATL Quantity')
    atl_payment_mode_id = fields.Many2one('payment.mode',  string='Mode of Payment')
    atl_depot_id = fields.Many2one('depot', string='Depot')
    atl_jetty_id = fields.Many2one('jetty', string='Jetty')
    atl_id = fields.Char(string='ATL ID')
    atl_approved_user_id = fields.Many2one('res.users',string='ATL Approved By')
    atl_date = fields.Date(string='ATL Date')



class SaleOrderLineLoading(models.Model):
    _inherit = "sale.order.line"

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.state not in ['sale','atl_approved'] or not line.product_id.type in ('consu','product'):
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_ticket_qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
            procurements.append(self.env['procurement.group'].Procurement(
                line.product_id, product_qty, procurement_uom,
                line.order_id.partner_shipping_id.property_stock_customer,
                line.name, line.order_id.name, line.order_id.company_id, values))

        if procurements:
            self.env['procurement.group'].run(procurements)
        return True

    @api.model
    def create(self, vals_list):
        lines = super(SaleOrderLineLoading, self).create(vals_list)
        lines.filtered(lambda line: line.state == 'atl_aaproved')._action_launch_stock_rule()
        return lines

    def write(self, values):
        lines = self.env['sale.order.line']
        if 'product_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            lines = self.filtered(
                lambda r: r.state in ['sale','atl_approved'] and not r.is_expense and float_compare(r.product_uom_qty, values['product_uom_qty'], precision_digits=precision) == -1)
        previous_product_uom_qty = {line.id: line.product_uom_qty for line in lines}
        res = super(SaleOrderLineLoading, self).write(values)
        if lines:
            lines._action_launch_stock_rule(previous_product_uom_qty)
        if 'customer_lead' in values and self.state in ['sale','atl_approved'] and not self.order_id.commitment_date:
            # Propagate deadline on related stock move
            self.move_ids.date_deadline = self.order_id.date_order + timedelta(days=self.customer_lead or 0.0)
        return res

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        deferred_revenue = self.product_id.product_deferred_revenue_id.account_unearned_revenue_id.id
        if not deferred_revenue:
            raise UserError(_('Please contact the Administrator to set the Unearned revenue account for %s', self.product_id.name))

        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id' : self.product_id.product_deferred_revenue_id.id,
            'account_id':deferred_revenue,
            'product_uom_id': self.product_uom.id,
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





    def action_view_order(self):
        order_id = self.mapped('order_id')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders')
        list_view_id = imd.xmlid_to_res_id('sale.view_order_tree')
        form_view_id = imd.xmlid_to_res_id('sale.view_order_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,

        }
        if len(order_id) > 1:
            result['domain'] = "[('id','in',%s)]" % order_id.id
        elif len(order_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = order_id.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result



    @api.depends('product_uom_qty','qty_delivered','transfer_created_qty','cancelled_remaining_qty')
    def _compute_procurement_qty(self):
        qty = 0.0
        for line in self:
            qty += line.product_uom_qty
            line.ticket_remaining_qty = line.product_uom_qty - line.ticket_created_qty - line.transfer_created_qty -line.cancelled_remaining_qty
            line.unloaded_balance_qty = line.ticket_created_qty - line.qty_delivered
            line.balance_qty = line.ticket_remaining_qty + line.unloaded_balance_qty
            line.balance_amt = line.balance_qty * line.price_unit


    ticket_created_qty = fields.Float(string='Ticketed Qty.', digits=dp.get_precision('Product Unit of Measure'),default=0.0,store=True)
    transfer_created_qty = fields.Float(string='Transferred Qty.', digits=dp.get_precision('Product Unit of Measure'),
                                       default=0.0)
    product_ticket_qty = fields.Float(string='Requested Qty.', digits=dp.get_precision('Product Unit of Measure'),default=0.0,store=True)
    ticket_remaining_qty = fields.Float(string='UnTicketed Qty.', compute='_compute_procurement_qty',digits=dp.get_precision('Product Unit of Measure'),default=0.0,store=True, help="Ordered Qty. - Ticketed Qty. - Transferred Qty. - Cancelled Qty. ")
    cancelled_remaining_qty = fields.Float(string='Cancelled Qty.',
                                        digits=dp.get_precision('Product Unit of Measure'), default=0.0)
    unloaded_balance_qty = fields.Float(string='Unloaded Ticketed Qty.', compute='_compute_procurement_qty', digits=dp.get_precision('Product Unit of Measure'),
                                      default=0.0, store=True,help="Ticketed Qty. - Loaded Qty.(Delivered)")
    balance_qty = fields.Float(string='Balance Qty.', compute='_compute_procurement_qty',
                                        digits=dp.get_precision('Product Unit of Measure'),
                                        default=0.0, store=True, help="Un-Ticketed Qty. + Un-Loaded Balance Qty.")
    balance_amt = fields.Float(string='Balance Amt', compute='_compute_procurement_qty', digits=dp.get_precision('Product Unit of Measure'), default=0.0, store=True)
    parent_sales_order_transfer_id = fields.Many2one('sale.order',related='order_id.parent_sales_order_transfer_id',store=True, string="Parent Sales Order Transfer")

    root_order_transfer_id = fields.Many2one('sale.order',related='order_id.root_order_transfer_id' , store=True,string='Root Transfer Sales Order')
    root_customer_id = fields.Many2one('res.partner',related='root_order_transfer_id.partner_id', store=True, string='Root Transfer Customer Name')
    advance_invoice_id = fields.Many2one(related="order_id.advance_invoice_id", string="Invoice", store=True)
    advance_invoice_name = fields.Char(related="advance_invoice_id.display_name", store=True, string="Invoice ID")
    is_throughput_order = fields.Boolean(related="order_id.is_throughput_order", string="Is throughput Order", store=True)
    is_internal_use_order = fields.Boolean(related="order_id.is_internal_use_order", string="Is Internal Use Order", store=True)



class ThroughputReceipt(models.Model):
    _name = 'kin.throughput.receipt'
    _inherit = ['mail.thread']
    _order = 'date_move desc'


    def unlink(self):
        for rec in self:
            if rec.state != 'draft' :
                # Don't allow deletion of throughput moves
                raise UserError(_('Sorry, Non-Draft throughput Movement cannot be deleted.'))

        return super(ThroughputReceipt, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('thru_move_code') or 'New'
        rec = super(ThroughputReceipt, self).create(vals)
        if not rec.customer_id.throughput_location_id :
            rec.customer_id.throughput_location_id = rec.destination_location_id
        return rec


    def write(self, vals):
        customer_id = vals.get('customer_id', False)
        destination_location_id = vals.get('destination_location_id', False)
        if customer_id and destination_location_id :
            self.env['res.partner'].browse(customer_id).throughput_location_id = destination_location_id

        res = super(ThroughputReceipt, self).write(vals)
        return res


    def action_confirm(self):

        if self.state == 'confirm':
            raise UserError(_('This record has been previously confirmed. Please refresh your browser'))

        return self.write({'state': 'confirm', 'user_id' : self.env.user.id,
                           'user_confirmed_date': datetime.today()})


    def action_validate(self):
        if self.state == 'validate':
            raise UserError(_('This record has been previously validated. Please refresh your browser'))

        if self.qty <= 0 :
            raise UserError(_('Sorry, you cannot receive qty that is less than  or equal to zero'))

        if self.operational_loss_perc <= 0:
            raise UserError(_('Sorry, Operational Loss Percentage cannot be less than or Equal to Zero'))

        # if self.operational_loss_cost <= 0:
        #     raise UserError(_('Sorry, Operational Loss Cost Price cannot be less than or Equal to Zero'))

       # create the stock move for the thruput qty
        stock_move_obj = self.env['stock.move']
        self.product_id.standard_price = 0
        vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            #'price_unit': 0,
            'date': self.date_move,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'product_uom_qty': self.qty,
            'origin': self.name
        }

        move_id = stock_move_obj.create(vals)
        move_id.action_confirm()
        move_id.force_assign()
        move_id.action_done()
        move_id.throughput_receipt_movement_id = self.id

        #Create move for operational loss to  stock
        # vals = {
        #     'name': self.name + ' Operational Loss',
        #     'product_id': self.product_id.id,
        #     'product_uom': self.product_id.uom_id.id,
        #     'price_unit': self.operational_loss_cost,
        #     'date': self.date_move,
        #     'location_id': self.source_location_id.id,
        #     'location_dest_id': self.destination_oper_loss_location_id.id,
        #     'product_uom_qty': self.operational_loss_qty,
        #     'origin': self.name
        # }
        #
        # move_id = stock_move_obj.create(vals)
        # move_id.action_confirm()
        # move_id.force_assign()
        # move_id.action_done()
        # move_id.throughput_receipt_movement_id = self.id

        self.sale_order_thruput_id = self.create_throughput_sales_order()
        self.sale_order_thruput_id.throughput_receipt_source_id = self
        self.sale_order_thruput_id.action_confirm_main_sale()


        self.invoice_id = self.create_customer_invoice()
        self.invoice_id.throughput_receipt_id = self

        partn_inv_ids = []
        user_names = ''
        group_obj = self.env.ref('account.group_account_invoice')
        msg = 'The Throughput Customer Invoice (%s) for (%s), has been created by %s' % (
            self.invoice_id.name, self.invoice_id.partner_id.name, self.env.user.name)
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_inv_ids.append(user.partner_id.id)

        if partn_inv_ids:
            self.message_post(
                _(msg),
                subject='%s' % msg, partner_ids=partn_inv_ids)

        #send notification
        partn_ids = []
        group_obj = self.env.ref(
            'kin_loading.group_throughput_receipt_validate_notification')
        msg = 'The Throughput Receipt (%s) for (%s), has been validated by %s' % (
            self.name, self.customer_id.name, self.env.user.name)
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_post(
                _(msg),
                subject='%s' % msg, partner_ids=partn_ids)
        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))



        return self.write({'state': 'validate', 'user_validate_id' : self.env.user.id,
                           'user_validated_date': datetime.today()})


    def create_throughput_sales_order(self):
        if not self.customer_id:
            raise UserError(_('Please set the customer for the throughput transfer'))
        lines = []

        line = (0, 0, {
                    'name': self.product_id.name,
                    'product_id': self.product_id.id,
                    'product_uom_qty': self.qty,
                    'product_uom': self.product_uom.id,
                    'price_unit': 0,
        })
        lines.append(line)

        sale_order_id = self.env['sale.order'].create({
            'partner_id': self.customer_id.id,
            'partner_invoice_id': self.customer_id.id,
            'partner_shipping_id': self.customer_id.id,
            'pricelist_id': self.customer_id.property_product_pricelist.id,
            'client_order_ref': self.name,
            'order_line': lines,
            'is_throughput_order':True
        })
        return sale_order_id



    def action_draft(self):
        self.state = 'draft'


    def btn_view_stock_move(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_move_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_move_ids')
    def _compute_stock_move_count(self):
        for rec in self:
            rec.stock_move_count = len(rec.stock_move_ids)


    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        customer = self.customer_id

        throughput_location = customer.throughput_location_id
        if customer and not throughput_location :
            stock_location = self.env['stock.location']
            parent_id = self.env['stock.location'].search([('is_throughput_parent_view', '=', True),('usage', '=', 'view')],limit=1)
            if not parent_id:
                raise UserError(_('Please contact the Administrator to set a parent location for throughput as view type '))
            vals = {
                'name': customer.name + ' Throughput Location',
                'usage': 'internal',
                'location_id' : parent_id.id,
                'is_throughput' : True,
            }
            stock_location_obj = stock_location.create(vals)
            throughput_location = stock_location_obj
            #customer.throughput_location_id = throughput_location  # this does not tend to save into partner id, which results to creation of duplicates location as you onchange the customer field
            customer.write({'throughput_location_id': throughput_location.id})

        self.destination_location_id = throughput_location

    def _compute_invoice_count(self):
        self.invoice_count = len(self.invoice_id)


    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_move_type': 'out_invoice',
        }
        if len(self) == 1:
            context.update({
                'default_partner_id': self.partner_id.id,
                'default_partner_shipping_id': self.partner_shipping_id.id,
                'default_invoice_payment_term_id': self.payment_term_id.id or self.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
                'default_invoice_origin': self.mapped('name'),
                'default_user_id': self.user_id.id,
            })
        action['context'] = context
        return action


    def action_view_invoice(self):
        invoice_id = self.mapped('invoice_id')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(invoice_id) > 1:
            result['domain'] = "[('id','in',%s)]" % invoice_id.id
        elif len(invoice_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = invoice_id.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    def send_email(self, grp_name, msg):
        # send email
        partn_ids = []
        group_obj = self.env.ref(grp_name)
        user_names = ''
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)

        if partn_ids:
            # self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=msg, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
        return


    def create_customer_invoice(self):

        inv_obj = self.env['account.move']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}

        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))

        invoice_vals = {
            'name': self.name ,
            'origin': self.name ,
            'type': 'out_invoice',
            'reference': self.name,
            'account_id': self.customer_id.property_account_receivable_id.id,
            'partner_id': self.customer_id.id,
            'journal_id': journal_id,
            'is_throughput_invoice': True,
            # 'company_id': sale_order.company_id.id,
            # 'user_id': self.confirmed_by and self.confirmed_by.id,
        }

        invoice = inv_obj.create(invoice_vals)

        # lines = []
        #
        # if not float_is_zero(1, precision_digits=precision):
        #     account = self.product_id.property_account_income_id
        #     if not account:
        #         raise UserError(
        #             _('Please define income account for this product: "%s" (id:%d)') % (
        #             self.product_id.name, self.product_id.id))
        #
        #
        #     default_analytic_account = self.env['account.analytic.default'].account_get(
        #         self.product_id.id, self.driver_id.id,
        #         self.confirmed_by.user_id.id, date.today())
        #
        #     inv_line = {
        #         'name': self.ticket_no,
        #         # 'sequence': self.sequence,
        #         'origin': self.ticket_no,
        #         'account_id': account.id,
        #         'price_unit': self.amount,
        #         'quantity': 1,
        #         'uom_id': self.product_id.uom_id.id,
        #         'product_id': self.product_id.id or False,
        #         'account_analytic_id':  default_analytic_account and default_analytic_account.analytic_id.id,
        #         'invoice_id': invoice.id
        #     }
        #     self.env['account.invoice.line'].create(inv_line)
        #
        #
        # if not invoice.invoice_line_ids:
        #     raise UserError(_('There is no invoiceable line.'))
        #     # If invoice is negative, do a refund invoice instead
        # if invoice.amount_untaxed < 0:
        #     invoice.type = 'out_refund'
        #     for line in invoice.invoice_line_ids:
        #         line.quantity = -line.quantity
        # # Use additional field helper function (for account extensions)
        # for line in invoice.invoice_line_ids:
        #     line._set_additional_fields(invoice)
        #     # Necessary to force computation of taxes. In account_invoice, they are triggered
        #     # by onchanges, which are not triggered when doing a create.
        # invoice.compute_taxes()

        group_name = 'account.group_account_invoice'
        msg = 'A Throughput Invoice (%s) for Customer (%s), has been Initiated by %s' % (
        invoice.name, invoice.partner_id.name, self.env.user.name)
        self.send_email(group_name, msg)

        return invoice


    def btn_view_sales_order(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Sales Order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.sale_order_thruput_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }


    @api.depends('sale_order_thruput_id')
    def _compute_so_count(self):
        for rec in self:
            rec.so_count = len(rec.sale_order_thruput_id)



    @api.depends('received_qty','operational_loss_perc')
    def _compute_throughput_qty(self):
        for rec in self:
            rec.qty = rec.received_qty - (rec.received_qty * (rec.operational_loss_perc / 100))

    @api.depends('received_qty', 'operational_loss_perc')
    def _compute_operational_loss_qty(self):
        for rec in self:
            rec.operational_loss_qty = rec.received_qty * (rec.operational_loss_perc / 100)

    def get_default_thruput_vendor_location(self):
        res = self.env['stock.location'].search([('is_throughput_vendor_location', '=', True)],limit=1)
        return res

    def get_default_oper_loss_location(self):
        res = self.env['stock.location'].search([('is_oper_loss_location', '=', True)],limit=1)
        return res

    name = fields.Char(string='Name',tracking=True)
    customer_id = fields.Many2one('res.partner',string='Throughput Customer')
    date_move = fields.Date(string='Date',
                                  default=lambda self: datetime.today().strftime('%Y-%m-%d'))
    source_location_id = fields.Many2one('stock.location', string='Source Location', ondelete='restrict',tracking=True,default=get_default_thruput_vendor_location)
    destination_location_id = fields.Many2one('stock.location', string='Destination Location',  ondelete='restrict',tracking=True)
    # destination_oper_loss_location_id  = fields.Many2one('stock.location',default=get_default_oper_loss_location,  string='Destination Location for Operational Loss', ondelete='restrict',tracking=True)
    product_id = fields.Many2one('product.product',string='Product', ondelete='restrict',tracking=True)
    product_uom = fields.Many2one('uom.uom', related='product_id.uom_id', string='Unit of Measure')
    received_qty = fields.Float('Received Qty.', digits=dp.get_precision('Product Price'),tracking=True)
    operational_loss_perc = fields.Float('Operational Loss %.', digits=dp.get_precision('Operational Loss Qty.'),
                                        tracking=True)
    operational_loss_qty = fields.Float('Operational Loss Qty.',compute="_compute_operational_loss_qty", digits=dp.get_precision('Operational Loss Qty.'),tracking=True)
    #operational_loss_cost = fields.Float(string='Operational Loss Cost Price')
    qty = fields.Float(string='Qty.', compute=_compute_throughput_qty, digits=dp.get_precision('Product Price'), tracking=True)
    stock_move_count = fields.Integer(compute="_compute_stock_move_count", string='# of Stock Moves', copy=False,default=0)
    stock_move_ids = fields.One2many('stock.move', 'throughput_receipt_movement_id', string='Stock Moves Entry(s)')
    sale_order_thruput_id = fields.Many2one('sale.order',string='Sales Order Throughput')
    so_count = fields.Integer(compute="_compute_so_count", string='# of Sales Order', copy=False,default=0)
    state = fields.Selection( [('draft', 'Draft'), ('confirm', 'Confirm'),('validate', 'Done'), ('cancel', 'Cancel')],  default='draft', tracking=True)
    note = fields.Text('Note')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id,
                              ondelete='restrict')
    user_confirmed_date = fields.Datetime('Confirmed Date')
    user_validate_id = fields.Many2one('res.users', string='User',
                              ondelete='restrict')
    user_validated_date = fields.Datetime('Validated Date')
    invoice_count = fields.Integer(compute="_compute_invoice_count", string='# of Invoices', copy=False, default=0)
    invoice_id = fields.Many2one('account.invoice')


class InternalUse(models.Model):
    _name = 'kin.internal.use'
    _inherit = ['mail.thread']
    _order = 'date_move desc'


    def action_confirm(self):
        if self.state == 'confirm':
            raise UserError(_('This record has been previously confirmed. Please refresh your browser'))
        return self.write({'state': 'confirm', 'user_id': self.env.user.id,'user_confirmed_date': datetime.today()})


    def action_validate(self):
        if self.state == 'validate':
            raise UserError(_('This record has been previously validated. Please refresh your browser'))

        if self.qty <= 0:
            raise UserError(_('Sorry, qty is less than  or equal to zero'))

        self.sale_order_internal_use_id = self.create_internal_use_sales_order()
        self.sale_order_internal_use_id.internal_use_source_id = self
        self.sale_order_internal_use_id.action_confirm_main_sale()

        # send notification
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref('kin_loading.group_internal_use_validate_notification')
        msg = 'The Internal Use transfer record (%s), has been validated by %s' % (
            self.name,  self.env.user.name)
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_post(
                body=_(msg),
                subject='%s' % msg, partner_ids=partn_ids)
        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        return self.write({'state': 'validate', 'user_validate_id': self.env.user.id,
                           'user_validated_date': datetime.today()})


    def create_internal_use_sales_order(self):
        if not self.source_location_id.is_internal_use_partner_id :
            raise UserError(_('Please contact the admin to set the internal use partner on the stock location configuration'))
        lines = []

        line = (0, 0, {
            'name': self.product_id.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.qty,
            'product_uom': self.product_uom.id,
            'price_unit': 0,
        })
        lines.append(line)

        partner_id = self.source_location_id.is_internal_use_partner_id
        sale_order_id = self.env['sale.order'].create({
            'partner_id': partner_id.id,
            'partner_invoice_id': partner_id.id,
            'partner_shipping_id': partner_id.id,
            'pricelist_id': partner_id.property_product_pricelist.id,
            'client_order_ref': self.name,
            'order_line': lines,
            'is_internal_use_order': True
        })
        return sale_order_id


    def action_draft(self):
        self.state = 'draft'


    def unlink(self):
        for rec in self:
            if rec.state != 'draft' :
                # Don't allow deletion of throughput moves
                raise UserError(_('Sorry, Non-Draft record cannot be deleted.'))

        return super(InternalUse, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('intu_code') or 'New'
        rec = super(InternalUse, self).create(vals)
        return rec


    def btn_view_sales_order(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Sales Order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.sale_order_internal_use_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('sale_order_internal_use_id')
    def _compute_so_count(self):
        for rec in self:
            rec.so_count = len(rec.sale_order_internal_use_id)

    name = fields.Char(string='Name')
    date_move = fields.Date(string='Date', default=lambda self: datetime.today().strftime('%Y-%m-%d'))
    source_location_id = fields.Many2one('stock.location', string='Source Location', ondelete='restrict')
    destination_location_id = fields.Many2one('stock.location', string='Destination Location', ondelete='restrict')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict')
    product_uom = fields.Many2one('uom.uom', related='product_id.uom_id', string='Unit of Measure')
    qty = fields.Float(string='Qty.',  digits=dp.get_precision('Product Price'), tracking=True)
    sale_order_internal_use_id = fields.Many2one('sale.order', string='Sales Order Internal')
    so_count = fields.Integer(compute="_compute_so_count", string='# of Sales Order', copy=False, default=0)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('validate', 'Done'), ('cancel', 'Cancel')], default='draft', tracking=True)
    note = fields.Text('Note')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, ondelete='restrict')
    user_confirmed_date = fields.Datetime('Confirmed Date')
    user_validate_id = fields.Many2one('res.users', string='User', ondelete='restrict')
    user_validated_date = fields.Datetime('Validated Date')


class ResCompanyTicket(models.Model):
    _inherit = "res.company"

    header_logo_loading = fields.Binary(string='Header Logo')
    header_data_loading = fields.Html(string='Header Data', help="e.g. Addresses of head Office and Tel No should be added here ")
    loading_tc_note = fields.Text(string='Loading Terms and Conditions', help="e.g. Terms and Conditions")
    is_generate_loading_date = fields.Boolean('Auto-Generate Loading Ticket Date')
    loading_date_interval = fields.Integer('Loading Ticket Date Interval', default=1)



class ProductProductLoading(models.Model):
    _inherit = 'product.template'

    white_product = fields.Selection([
        ('pms', 'PMS'),
        ('ago', 'AGO'),
        ('kero', 'DPK'),
        ('atk', 'ATK'),
        ('lpfo', 'L.P.F.O')
    ], string='White Product')

    account_unearned_revenue_id = fields.Many2one('account.account',string='Unearned Revenue Account' )
    is_deferred_revenue = fields.Boolean(string='Is Deferred Revenue')
    product_deferred_revenue_id = fields.Many2one('product.template', string='Product Deferred Revenue')


class Depot(models.Model):
    _name = 'depot'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _inherits = {'stock.location': 'stock_location_tmpl_id'}

    @api.depends('stock_location_tmpl_id')
    def _compute_stock_location_count(self):
        for rec in self:
            rec.stock_location_count = len(rec.stock_location_tmpl_id)

    def btn_view_stock_location(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Location'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.location',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_location_tmpl_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),

        }

    # name = fields.Char('Tank No.')
    #product_id = fields.Many2one('product.product', string='Product')
   # product_uom = fields.Many2one('uom.uom', related='product_id.uom_id', string='Unit')
    stock_location_count = fields.Integer(compute="_compute_stock_location_count", string='# of Stock Locations',
                                          copy=False, default=0)
    stock_location_tmpl_id = fields.Many2one('stock.location', 'Stock Location Template', required=True,ondelete="cascade", select=True, auto_join=True)
    sale_order_ids = fields.One2many('sale.order','atl_depot_id', string='Sales Orders')
    purchase_order_ids = fields.One2many('purchase.order', 'depot_id', string='Purchase Orders')



class Jetty(models.Model):
    _name = 'jetty'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Jetty')
    description = fields.Text(string='Description')


class PaymentMode(models.Model):
    _name = 'payment.mode'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Name')

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        if not self.depot_id :
            raise UserError('Kindly set the depot for the product receipt')
        ctx = {
            'depot_id': self.depot_id.stock_location_tmpl_id.id
        }
        res = super(PurchaseOrder, self.with_context(ctx)).button_confirm()
        return res

    depot_id = fields.Many2one('depot', string='Depot')


class DRPInfo(models.Model):
    _name = 'dpr.info'
    _rec_name = 'address'
    _description = 'DRP Information'

    customer_id = fields.Many2one('res.partner',string='Customer')
    address = fields.Char(string='Destination')
    dpr_no = fields.Char('DPR License No.')
    dpr_expiry_date = fields.Date('DPR Expiry Date')
    picking_ids = fields.One2many('stock.picking','dpr_info_id',string='Stock Pickings')



class ResPartner(models.Model):
    _inherit = 'res.partner'

    def send_mass_email_sot(self):
        company_email = self.env.user.company_id.email.strip()

        for partner in self:
            partner_email = partner.email or False

            if company_email and partner_email:
                mail_template = partner.env.ref('kin_loading.mail_templ_sot_email')
                mail_template.send_mail(partner.id, force_send=False)
        return

    throughput_location_id = fields.Many2one('stock.location',string='Throughput Location')
    dpr_info_ids = fields.One2many('dpr.info','customer_id',string='DPR Informations')


