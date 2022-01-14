# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017 - 2021  Kinsolve Solutions
# Copyright 2017 - 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"
    _order = 'name desc'

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        # set picking document links
        scraps = self.env['stock.scrap'].search([('picking_id', '=', self.id)])
        valuation_layers =  (self.move_lines + scraps.move_id).stock_valuation_layer_ids
        for valuation in valuation_layers :
            valuation.account_move_id.picking_id = self
        return res

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

    def _compute_account_move_count(self):
        for rec in self:
            moves = rec.mapped('move_ids')
            rec.move_count = len(moves)


    def btn_view_jnr(self):
        """ This function returns an action that display existing picking orders of given purchase order ids. When only one found, show the picking immediately.
        """
        result = self.env["ir.actions.actions"]._for_xml_id('account.action_move_journal_line')
        # override the context to get rid of the default filtering on operation type
        result['context'] = {'default_partner_id': self.partner_id.id, 'default_origin': self.name, }
        move_ids = self.mapped('move_ids')
        # choose the view_mode accordingly
        if not move_ids or len(move_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (move_ids.ids)
        elif len(move_ids) == 1:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state,view) for state,view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = move_ids.id
        return result




    invoice_id = fields.Many2one('account.move' , copy=False)
    invoice_count = fields.Integer(compute="_compute_invoice_count", string='# of Invoices', copy=False, default=0, store=True)
    purchase_id = fields.Many2one('purchase.order', copy=False,)
    po_count = fields.Integer(compute="_compute_po_count", string='# of Purchase Orders', copy=False, default=0, store=True)
    sale_id = fields.Many2one('sale.order', copy=False,)
    so_count = fields.Integer(compute="_compute_so_count", string='# of Sales Orders', copy=False, default=0, store=True)
    move_ids = fields.One2many('account.move', 'picking_id', copy=False, )
    move_count = fields.Integer(compute="_compute_account_move_count", string='# of Jornal Entries', copy=False, default=0)