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
            if not self.aftershore_receipt_documents :
                raise UserError('Kindly upload the aftershore receipt documents')

        return res

    aftershore_receipt_documents = fields.Binary(string='After Shore Receipt Documents')




class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    @api.onchange('department_id')
    def _onchange_conv_rate(self):
        self.assigned_to = self.sudo().department_id.manager_id.user_id

    department_id = fields.Many2one('hr.department', string='Department')