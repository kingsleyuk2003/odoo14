# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2021  Kinsolve Solutions
# Copyright 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date, timedelta

class AccountMove(models.Model):
    _inherit = 'account.move'

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

    def button_draft(self):
        self.is_request_approval_sent = False
        self.is_request_approval_by = False
        self.is_request_approval_date = False
        return super(AccountMove, self).button_draft()

    def btn_request_approval(self):
        if self.state == 'posted':
            raise UserError('Sorry, the record has already been posted')
        if self.state == 'cancel':
            raise UserError('Sorry, the record is cancelled')

        doc_type = ''
        grp = ''
        if self.move_type == 'out_invoice':
            doc_type = 'Invoice'
            grp = 'kin_account.group_account_move_receive_request_approval_invoice_email'
        elif self.move_type == 'out_refund':
            doc_type = 'Credit Note'
            grp = 'kin_account.group_account_move_receive_request_approval_invoice_email'
        elif self.move_type == 'in_invoice':
            doc_type = 'Bill'
            grp = 'kin_account.group_account_move_receive_request_approval_bill_email'
        elif self.move_type == 'in_refund':
            doc_type = 'Debit Note'
            grp = 'kin_account.group_account_move_receive_request_approval_bill_email'
        elif self.move_type == 'entry':
            doc_type = 'Journal Entry'
            grp = 'kin_account.group_account_move_receive_request_approval_entry_email'

        msg = '%s Entry (%s) from %s requires your approval' % (doc_type,self.name, self.env.user.name)
        self.send_grp_email(grp_name=grp, subject=msg, msg=msg)


        self.is_request_approval_sent = True
        self.is_request_approval_by = self.env.user
        self.is_request_approval_date = fields.Datetime.now()

    is_request_approval_sent = fields.Boolean(string='Is Request Approval Sent', copy=False, tracking=True)
    is_request_approval_by = fields.Many2one('res.users', string='Requested By', copy=False, tracking=True)
    is_request_approval_date = fields.Datetime(string='Request Approval Date', copy=False, tracking=True)

    def action_view_po(self):
        action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_form_action")
        action['views'] = [
            (self.env.ref('purchase.purchase_order_view_tree').id, 'tree'),
        ]
        action['context'] = self.env.context
        po_ids = self.mapped('purchase_ids')
        action['domain'] = [('id', 'in',  [x.id for x in self.purchase_ids])]

        if len(po_ids) > 1:
            action['domain'] = [('id', 'in',  [x.id for x in self.purchase_ids])]
        elif len(po_ids) == 1:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form'),]
            action['res_id'] = self.purchase_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


    @api.depends('purchase_ids')
    def _compute_po_count(self):
        for rec in self:
            rec.po_count = len(rec.purchase_ids)

    @api.depends('sale_ids')
    def _compute_so_count(self):
        for rec in self:
            rec.so_count = len(rec.sale_ids)

    def action_view_so(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action['views'] = [
            (self.env.ref('sale.view_order_tree').id, 'tree'),
        ]
        action['context'] = self.env.context
        sale_ids = self.mapped('sale_ids')
        action['domain'] = [('id', 'in',  [x.id for x in self.sale_ids])]

        if len(sale_ids) > 1:
            action['domain'] = [('id', 'in',  [x.id for x in self.sale_ids])]
        elif len(sale_ids) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form'),]
            action['res_id'] = sale_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action




    def action_view_invoices(self):
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



    def _compute_picking_count(self):
        for rec in self:
            pickings = rec.mapped('picking_ids')
            rec.picking_count = len(pickings)

    def action_view_picking(self):
        """ This function returns an action that display existing picking orders of given purchase order ids. When only one found, show the picking immediately.
        """
        result = self.env["ir.actions.actions"]._for_xml_id('stock.action_picking_tree_all')
        # override the context to get rid of the default filtering on operation type
        result['context'] = {'default_partner_id': self.partner_id.id, 'default_origin': self.name, }
        pick_ids = self.mapped('picking_ids')
        # choose the view_mode accordingly
        if not pick_ids or len(pick_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state,view) for state,view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = pick_ids.id
        return result

    def replace_amount_to_text(self,amt,currency=False):
        big = ''
        small = ''
        if currency.name == 'NGN' :
            big = 'Naira'
            small = 'kobo'
        elif currency.name == 'USD':
            big = 'Dollar'
            small = 'Cent'
        else :
            big = 'Naira'
            small = 'kobo'

        amount_text = currency.amount_to_text(amt).replace('euro',big).replace('Cent',small)
        return str.upper('  **** ' + amount_text + '**** ONLY')


    @api.depends('amount_total')
    def _compute_amount_in_words(self):
        for rec in self:
            current_curr = self.currency_id
            if current_curr:
                #amount_in_words = current_curr.amount_to_text(self.move_ids_without_package[0].quantity_done)
                rec.amount_in_words = rec.replace_amount_to_text(rec.amount_total,current_curr)
            else:
                rec.amount_in_words = False


    @api.depends('amount_total')
    def _compute_description_report(self):
        desc = ''
        count = 0
        for line in self.invoice_line_ids:
            if not line.exclude_from_invoice_tab :
                count += 1
                sym = line.currency_id.symbol
                desc += "<br>%s.) Product:%s   Qty:%s %s   Price:%s%s   Subtotal:%s%s" % (count,line.name, line.quantity,line.product_uom_id.name,sym,line.price_unit,sym,line.price_subtotal)
            self.description_report = desc

    @api.onchange('partner_id_customer')
    def _compute_partner_id_customer(self):
        for pay in self:
            pay.partner_id = pay.partner_id_customer

    @api.onchange('partner_id_supplier')
    def _compute_partner_id_supplier(self):
        for pay in self:
            pay.partner_id = pay.partner_id_supplier



    amount_in_words = fields.Char(string="Amount in Words", store=True, compute='_compute_amount_in_words')
    description_report = fields.Text(string='Move Description', store=True, compute='_compute_description_report')
    journal_id = fields.Many2one(tracking=True)
    ref = fields.Char(tracking=True)
    date = fields.Date(tracking=True)
    line_ids = fields.One2many(tracking=True)
    partner_id = fields.Many2one(tracking=True)
    amount_total = fields.Monetary(tracking=True)
    amount_residual = fields.Monetary(tracking=True)
    # narration = fields.Text(string='Internal Note')
    company_id = fields.Many2one(tracking=True)
    state = fields.Selection(tracking=True)

    picking_ids = fields.One2many('stock.picking','invoice_id',copy=False, )
    picking_count = fields.Integer(compute="_compute_picking_count", string='# of Delivery Notes', copy=False, default=0)
    purchase_ids = fields.Many2many('purchase.order', 'purchase_account_move','account_id' , 'purchase_id',   string='Purchase Order', copy=False)
    po_count = fields.Integer(compute="_compute_po_count", string='# of Purchase Orders', copy=False, default=0)
    sale_ids = fields.Many2many("sale.order", 'sales_account_move_rel', 'sale_id', 'account_id', string='Sales Orders',copy=False, )
    so_count = fields.Integer(compute="_compute_so_count", string='# of Sales Orders', copy=False, default=0)
    payment_id = fields.Many2one('account.payment',string='Payment')
    picking_id = fields.Many2one('stock.picking', string='Transfer Document')
    partner_id_customer = fields.Many2one(related='partner_id', readonly=False, check_company=True, string="Customer")
    partner_id_supplier = fields.Many2one(related='partner_id', readonly=False, check_company=True, string="Vendor")




