# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    via = fields.Char(string='Via', tracking=True)
    po_number = fields.Char(related='picking_do_id.po_number',string='PO Number', store=True)
    do_number = fields.Char(string='DO Number')
    picking_do_id = fields.Many2one('stock.picking',string='Delivery Order')
    is_charge_bill = fields.Boolean(string='Is Charge Bill')
