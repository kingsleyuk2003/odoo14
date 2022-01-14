# -*- coding: utf-8 -*-

from openerp import api, fields, models

class CreateAdvanceInvoiceWizard(models.TransientModel):
    _name = 'create.advance.invoice.wizard'
    _description = 'Create Advance Invoice Wizard'


    def action_advance_invoice_wizard(self):
        rec_ids = self.env.context['active_ids']
        records = self.env['sale.order'].browse(rec_ids)
        for rec in records :
            rec.action_create_advance_invoice()
        return

    sale_amount= fields.Float(string='Sales Amount')


