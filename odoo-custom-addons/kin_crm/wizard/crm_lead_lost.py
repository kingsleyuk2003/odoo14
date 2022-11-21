# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'


    def action_lost_reason_apply(self):
        active_ids = self.env.context.get('active_ids')
        crm_leads = self.env['crm.lead'].browse(active_ids)
        for crm_lead in crm_leads:
            crm_lead.order_ids.unlink()
        return super(CrmLeadLost, self).action_lost_reason_apply()
