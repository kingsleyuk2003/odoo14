# -*- coding: utf-8 -*-

from odoo import api, fields, models

class mass_confirm_order_wizard(models.TransientModel):
    _name = 'mass.confirm.order.wizard'
    _description = 'Mass Email Payslip Wizard'

    
    def mass_confirm_product_order(self):
        rec_ids = self.env.context['active_ids']
        orders = self.env['sale.order'].browse(rec_ids)
        for order in orders:
            order.action_confirm_main_sale()
        return
