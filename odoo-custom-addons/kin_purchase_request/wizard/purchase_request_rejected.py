# -*- coding: utf-8 -*-

from odoo import api, fields, models

class purchase_request_reject_wizard(models.TransientModel):
    _name = 'purchase.request.reject.wizard'
    _description = 'Purchase Request Reject Wizard'

    
    def reject_purchase_request(self):
        ids = self.env.context['active_ids']
        msg = self.msg
        purchase_requests = self.env['purchase.request'].browse(ids)
        for pr in purchase_requests :
            pr.action_reject(msg)
        return

    msg = fields.Text(string='Reason for Rejection', required=True)
