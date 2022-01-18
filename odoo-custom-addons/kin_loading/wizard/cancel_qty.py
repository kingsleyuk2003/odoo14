# -*- coding: utf-8 -*-

from odoo import api, fields, models

class CancelQtyWizard(models.TransientModel):
    _name = 'cancel.qty.wizard'

    def action_cancel_qty(self):
        rec_ids = self.env.context['active_ids']
        is_cancel_unloaded_unticketed_qty = self.is_cancel_unloaded_unticketed_qty
        records = self.env['sale.order'].browse(rec_ids)
        for rec in records:
            rec.action_cancel_balance_order(is_cancel_unloaded_unticketed_qty)
        return

    is_cancel_unloaded_unticketed_qty = fields.Selection([
        ('select_one','Please Select one of the Cancellation Type Below'),
         ('unloaded_cancel', 'Cancel Ticketed Qty. that has not been Loaded and UnTicketed Qty.'),
        ('unticketed_cancel', 'Cancel Only UnTicketed Qty.')
    ], string='Product Qty. Cancellation Type', default='select_one',tracking=True)
