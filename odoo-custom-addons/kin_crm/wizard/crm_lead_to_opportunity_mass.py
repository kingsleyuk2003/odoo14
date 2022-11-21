# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Lead2OpportunityMassConvert(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner.mass'

    action = fields.Selection(default='nothing')
    deduplicate = fields.Boolean( default=False)

