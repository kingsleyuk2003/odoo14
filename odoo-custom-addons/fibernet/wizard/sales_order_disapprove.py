# -*- coding: utf-8 -*-

from odoo import api, fields, models

class sales_order_disaaprove_wizard(models.TransientModel):
    _name = 'sale.order.disapprove.wizard'
    _description = 'Sales Order Disapprove Wizard'

    
    def disapprove_sales_orders(self):
        sale_ids = self.env.context['active_ids']
        msg = self.msg
        sale_orders = self.env['sale.order'].browse(sale_ids)
        for order in sale_orders :
            order.action_disapprove(msg)
        return

    msg = fields.Text(string='Reason for Disapproval', required=True)
