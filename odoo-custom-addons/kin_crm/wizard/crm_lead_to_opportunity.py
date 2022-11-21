# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class crm_lead2opportunity_mass_convert(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner.mass'

    action = fields.Selection(default='nothing')

class crm_lead2opportunity_partner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'


    name = fields.Selection([
        ('convert', 'Convert to opportunity')
    ], 'Conversion Action',  readonly=True, store=True, compute_sudo=False)

    action = fields.Selection(default='nothing')

    # def default_get(self, cr, uid, fields, context=None):
    #     """
    #     Default get for name, opportunity_ids.
    #     If there is an exisitng partner link to the lead, find all existing
    #     opportunities links with this partner to merge all information together
    #     """
    #     lead_obj = self.pool.get('crm.lead')
    #
    #     res = super(crm_lead2opportunity_partner, self).default_get(cr, uid, fields, context=context)
    #     if context.get('active_id'):
    #         tomerge = [int(context['active_id'])]
    #
    #         partner_id = res.get('partner_id')
    #         lead = lead_obj.browse(cr, uid, int(context['active_id']), context=context)
    #         email = lead.partner_id and lead.partner_id.email or lead.email_from
    #
    #         tomerge.extend(self._get_duplicated_leads(cr, uid, partner_id, email, include_lost=True, context=context))
    #         tomerge = list(set(tomerge))
    #
    #         if 'action' in fields and not res.get('action'):
    #             res.update({'action' : partner_id and 'exist' or 'create'})
    #         if 'partner_id' in fields:
    #             res.update({'partner_id' : partner_id})
    #         if 'name' in fields:
    #             res.update({'name' : len(tomerge) >= 2 and 'convert' or 'convert'})
    #         # if 'opportunity_ids' in fields and len(tomerge) >= 2:
    #         #     res.update({'opportunity_ids': tomerge})
    #         if lead.user_id:
    #             res.update({'user_id': lead.user_id.id})
    #         if lead.team_id:
    #             res.update({'team_id': lead.team_id.id})
    #         if not partner_id and not lead.contact_name:
    #             res.update({'action': 'nothing'})
    #     return res
    #
    #
    # def _create_partner(self, cr, uid, lead_id, action, partner_id, context=None):
    #     """
    #     Create partner based on action.
    #     :return dict: dictionary organized as followed: {lead_id: partner_assigned_id}
    #     """
    #     #TODO this method in only called by crm_lead2opportunity_partner
    #     #wizard and would probably diserve to be refactored or at least
    #     #moved to a better place
    #     if context is None:
    #         context = {}
    #     lead = self.pool.get('crm.lead')
    #     if action == 'each_exist_or_create':
    #         ctx = dict(context)
    #         ctx['active_id'] = lead_id
    #         partner_id = self._find_matching_partner(cr, uid, context=ctx)
    #         action = 'create'
    #     partner_id = False
    #     res = lead.handle_partner_assignation(cr, uid, [lead_id], action, partner_id, context=context)
    #     return res.get(lead_id)
