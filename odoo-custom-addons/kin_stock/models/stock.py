# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017 - 2021  Kinsolve Solutions
# Copyright 2017 - 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = "stock.move"



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

        self.create_sales_invoice()
        self.create_purchase_bill()

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
