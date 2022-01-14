# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models

class stock_picking_reject_wizard(models.TransientModel):
    _name = 'stock.picking.reject.wizard'
    _description = 'Stock Picking Reject Wizard'

    
    def action_wizard_reject_notice(self):
        picking_ids = self.env.context['active_ids']
        msg = self.msg
        pickings = self.env['stock.picking'].browse(picking_ids)
        for pick in pickings :
            pick.action_reject_notice(msg)
        return

    msg = fields.Text(string='Reason for Rejection', required=True)
