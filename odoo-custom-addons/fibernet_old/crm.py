# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from datetime import datetime, timedelta
from odoo import SUPERUSER_ID
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from urllib import urlencode
from urlparse import urljoin
import time
from odoo import tools, api


class ProductTemplateExtend(models.Model):
    _inherit = 'product.template'

    is_mrc = fields.Boolean(string='Is MRC', track_visibility='always')


class CRMUserTarget(models.Model):
    _inherit = 'crm.user.target'

    @api.depends('target_opportunity')
    def _amount_all(self):
        for rec in self:
            start_date = rec.start_date
            end_date = rec.end_date
            opportunity_target = rec.target_opportunity
            actual_won_opportunity_revenue = 0
            perc_opportunity_target_won = 0

            crm_lead_obj = rec.env['crm.lead'].search([
                ('stage_id.probability', '=', '100'),
                ('date_won', '>=', start_date), ('date_won', '<=', end_date),
                ('user_id', '=', rec.user_id.id)
            ])
            total_amount_untaxed = 0

            for crm_lead in crm_lead_obj:
                total_amount_untaxed += sum(
                    crm_lead.product_line_ids.filtered(
                        lambda line: line.product_id.is_mrc == True).mapped(
                            'price_total'))

                actual_won_opportunity_revenue = total_amount_untaxed
                if opportunity_target:
                    perc_opportunity_target_won = (
                        actual_won_opportunity_revenue /
                        opportunity_target) * 100
                else:
                    perc_opportunity_target_won = 0
            rec.update({
                'actual_won_opportunity_revenue':
                actual_won_opportunity_revenue,
                'perc_opportunity_target_won':
                perc_opportunity_target_won,
            })


class CRMTargetOpportunity(models.Model):
    _inherit = 'crm.target.opportunity'

    
    def run_check_target_analysis(self):
        target_recs = self.search([])
        for target_rec in target_recs:
            target_rec.btn_target_compute()
        return True

    
    def btn_target_compute(self):
        start_date = self.start_date
        end_date = self.end_date
        sales_team = self.sales_team
        total_opportunity_target = 0
        total_actual_won_opportunity_revenue = 0
        total_perc_opportunity_target_won = 0
        self.target_lines_ids.unlink()

        for member in sales_team.member_ids:
            total_amount_taxed = 0
            crm_lead_obj = self.env['crm.lead'].search([
                ('stage_id.probability', '=', '100'),
                ('date_won', '>=', start_date), ('date_won', '<=', end_date),
                ('user_id', '=', member.id)
            ])
            for crm_lead in crm_lead_obj:
                # total_amount_taxed +=  crm_lead.product_line_ids.filtered(lambda line: line.product_id.is_mrc == True).mapped('price_total')[0] #raised error if the list is empty, so the safest option is to use the sum() function
                # OR
                total_amount_taxed += sum(
                    crm_lead.product_line_ids.filtered(
                        lambda line: line.product_id.is_mrc == True).mapped(
                            'price_total'))

            crm_user_target_obj = self.env['crm.user.target'].search([
                ('start_date', '>=', start_date), ('end_date', '<=', end_date),
                ('user_id', '=', member.id)
            ])
            opportunity_target = 0
            for crm_user_target in crm_user_target_obj:
                opportunity_target += crm_user_target.target_opportunity

            actual_won_opportunity_revenue = total_amount_taxed
            if opportunity_target:
                perc_opportunity_target_won = (actual_won_opportunity_revenue /
                                               opportunity_target) * 100
            else:
                perc_opportunity_target_won = 0

            total_opportunity_target += opportunity_target
            total_actual_won_opportunity_revenue += actual_won_opportunity_revenue
            if total_opportunity_target:
                total_perc_opportunity_target_won = (
                    total_actual_won_opportunity_revenue /
                    total_opportunity_target) * 100
            else:
                total_perc_opportunity_target_won = 0

            self.env['crm.target.opportunity.lines'].create({
                'user_id':
                member.id,
                'opportunity_target':
                opportunity_target,
                'actual_won_opportunity_revenue':
                actual_won_opportunity_revenue,
                'perc_opportunity_target_won':
                perc_opportunity_target_won,
                'crm_target_opportunity_id':
                self.id
            })
            self.write({
                'total_opportunity_target':
                total_opportunity_target,
                'total_actual_won_opportunity_revenue':
                total_actual_won_opportunity_revenue,
                'total_perc_opportunity_target_won':
                total_perc_opportunity_target_won
            })


class CrmLeadExtend(models.Model):
    _inherit = 'crm.lead'

    @api.onchange('company_id')
    def onchange_company(self):
        company_id = self.company_id
        if company_id and company_id.company_select == 'kkon':
            self.customer_type = 'kkon'
        elif company_id and company_id.company_select == 'fob':
            self.customer_type = 'fob'

    def _lead_create_contact(self,
                             cr,
                             uid,
                             lead,
                             name,
                             is_company,
                             parent_id=False,
                             context=None):
        partner = self.pool.get('res.partner')
        vals = {
            'name':
            name,
            'user_id':
            lead.user_id.id,
            'comment':
            lead.description,
            'team_id':
            lead.team_id.id or False,
            'parent_id':
            parent_id,
            'phone':
            lead.phone,
            'mobile':
            lead.mobile,
            'email':
            tools.email_split(lead.email_from)
            and tools.email_split(lead.email_from)[0] or False,
            'fax':
            lead.fax,
            'title':
            lead.title and lead.title.id or False,
            'function':
            lead.function,
            'street':
            lead.street,
            'street2':
            lead.street2,
            'zip':
            lead.zip,
            'city':
            lead.city,
            'country_id':
            lead.country_id and lead.country_id.id or False,
            'state_id':
            lead.state_id and lead.state_id.id or False,
            'is_company':
            is_company,
            'type':
            'contact',
            'company_id':
            lead.company_id.id,
            'contact_person':
            lead.contact_name,
            'customer_type':
            lead.customer_type,
            'is_upcountry':
            lead.is_upcountry,
            'first_name':
            lead.first_name,
            'last_name':
            lead.last_name,
            'gender':
            lead.gender,
            'estate_id':
            lead.estate_id and lead.estate_id.id or False,
            'city_cust':
            lead.city_cust,
            'dob':
            lead.dob,
            'state_ng':
            lead.state_ng,
        }
        partner = partner.create(cr, uid, vals, context=context)
        return partner

    def _create_lead_partner(self, cr, uid, lead, context=None):
        if lead.partner_name:
            partner_company_id = self._lead_create_contact(cr,
                                                           uid,
                                                           lead,
                                                           lead.partner_name,
                                                           True,
                                                           context=context)
        elif lead.partner_id:
            partner_company_id = lead.partner_id.id
        else:
            partner_company_id = False

        partner_id = partner_company_id or self._lead_create_contact(
            cr, uid, lead, lead.name, False, context=context)
        return partner_id

    
    def action_create_customer(self):
        ctx = dict(self._context)
        if not self.team_id:
            raise UserError(_('Please set a Sales Team for this Opportunity'))
        ctx['company_id'] = self.team_id.company_id.id

        if not self.partner_id:
            lead_id = self.id
            ctx['active_id'] = lead_id
            ctx['active_model'] = 'crm.lead'
            #partner_id = self.env['crm.lead2opportunity.partner'].with_context(ctx)._find_matching_partner()
            res = self.handle_partner_assignation('create', partner_id=False)
            part_id = res.get(lead_id)
            self.env['res.partner'].browse(part_id).active = True

            # notify responsible people
            partner_obj = self.env['res.partner'].browse(part_id)
            user_ids = []
            group_obj = self.env.ref(
                'kin_crm.group_receive_new_customer_from_lead')
            user_names = ''
            for user in group_obj.users:
                user_names += user.name + ", "
                user_ids.append(user.id)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_(
                'A New Customer (%s) has been created for the CRM Opportunity with id - %s, from %s'
            ) % (partner_obj.name, self.name, self.env.user.name),
                              subject='A Customer has been created',
                              subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info(
                '%s Will Be Notified by Email for Customer Created' %
                (user_names))

            return part_id


    
    def create_quotation(self):

        #send email to sales team leader
        leader_id = self.team_id.user_id
        if not leader_id:
            raise UserError(
                _('Please contact the admin to set the team leader'))

        user_name = leader_id.name
        msg = _(
            'A New Quotation from CRM Opportunity has been created by %s, from the Opportunity - %s, for customer %s'
        ) % (self.env.user.name, self.name, self.partner_id.name)

        self.message_post(_(msg),
                          subject='%s' % msg,
                          partner_ids=[leader_id.partner_id.id])
        self.env.user.notify_info('%s Will Be Notified by Email' % (user_name))

        res = super(CrmLeadExtend, self).create_quotation()
        if self.is_upcountry:
            res.is_upcountry = True

        return res

    
    def action_view_ticket(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Ticket'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.ticket',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.ticket_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        for rec in self:
            rec.ticket_count = len(rec.ticket_ids)

    
    def action_create_survey_ticket(self, msg):
        if len(self.ticket_ids) > 0:
            raise UserError(
                _('Sorry, you can only generate a survey ticket once.'))
        res = {}
        self.state = 'survey_ticket'
        name = 'Survey Ticket for ' + self.name

        csc = False
        is_default_survey_group = False
        if self.customer_type == 'fob':
            # assign default survey ticket group for csc fob
            is_default_survey_group = self.env['user.ticket.group'].search(
                [('is_survey_group_default_csc_fob', '=', True)], limit=1)

            if not is_default_survey_group:
                raise UserError(
                    _('Please contact the Admin to set the Default survey group for CSC FOB'
                      ))
            if is_default_survey_group:
                csc = is_default_survey_group.id
                name = 'FOB Survey Ticket for ' + self.name
        elif self.customer_type == 'kkon':
            is_default_survey_group = self.env['user.ticket.group'].search(
                [('is_survey_group_default_csc_kkon', '=', True)], limit=1)

            if not is_default_survey_group:
                raise UserError(
                    _('Please contact the Admin to set the Default survey group for CSC KKONTech'
                      ))
            if is_default_survey_group:
                csc = is_default_survey_group.id
                name = 'KKONTech Survey Ticket for ' + self.name
        else:
            raise UserError(_('No FOB or KKON Customer Type Selected.'))

        category_id = self.env.ref('kkon_modifications.kkon_survey')
        # Create ticket
        vals = {
            'name': name,
            'category_id': category_id.id,
            'partner_id': self.partner_id and self.partner_id.id or False,
            'location_id': self.partner_id.location_id.id,
            'base_station_id': self.partner_id.base_station_id.id,
            'initiator_ticket_group_id': csc,
            'description': msg,
        }
        ticket_obj = self.env['kin.ticket'].create(vals)
        ticket_obj.crm_id = self.id

        partn_ids = []
        user_names = ''
        if is_default_survey_group:
            # send group email
            users = is_default_survey_group.sudo().user_ids
            for user in users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

            if partn_ids:
                msg = _(
                    'A New Survey Ticket has been created with subject (%s), from %s'
                ) % (self.name, self.env.user.name)
                self.message_post(msg,
                                  subject=msg,
                                  partner_ids=partn_ids,
                                  subtype_xmlid='mail.mt_comment', force_send=False)
                self.env.user.notify_info(
                    '%s Will Be Notified by Email for Survey Ticket Created' %
                    (user_names))

        return res

    ticket_ids = fields.One2many('kin.ticket', 'crm_id', string='Tickets')
    ticket_count = fields.Integer(compute="_compute_ticket_count",
                                  string='# of Ticket',
                                  copy=False,
                                  default=0)
    is_survey_ticket_close = fields.Boolean(string='Survey Ticket Closed')
    customer_type = fields.Selection([('kkon', 'KKONTECH'), ('fob', 'FOB'),
                                      ('reseller', 'Reseller'),
                                      ('carrier', 'Carrier')],
                                     string='Customer Type')
    is_upcountry = fields.Boolean(string='Up Country Transaction')
    is_company = fields.Boolean(string='Is a Company')
    is_estate = fields.Boolean(string='Is an Estate')

    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')],
                              string='Gender')
    estate_id = fields.Many2one('kkon.estate', string='Estate')
    city_cust = fields.Char(string='City')
    dob = fields.Date(string="DOB")
    state_ng = fields.Selection([('Abia', 'Abia'),
                                 ('FCT', 'Abuja Federal Capital Territory'),
                                 ('Akwa Ibom', 'Akwa Ibom'),
                                 ('Anambra', 'Anambra'), ('Bauchi', 'Bauchi'),
                                 ('Bayelsa', 'Bayelsa'), ('Benue', 'Benue'),
                                 ('Borno', 'Borno'),
                                 ('Cross River', 'Cross River'),
                                 ('Delta', 'Delta'), ('Ebonyi', 'Ebonyi'),
                                 ('Edo', 'Edo'), ('Ekiti', 'Ekiti'),
                                 ('Enugu', 'Enugu'), ('Gombe', 'Gombe'),
                                 ('Imo', 'Imo'), ('Jigawa', 'Jigawa'),
                                 ('Kaduna', 'Kaduna'), ('Kano', 'Kano'),
                                 ('Katsina', 'Katsina'), ('Kebbi', 'Kebbi'),
                                 ('Kogi', 'Kogi'), ('Kwara', 'Kwara'),
                                 ('Lagos', 'Lagos'), ('Nasarawa', 'Nasarawa'),
                                 ('Niger', 'Niger'), ('Ogun', 'Ogun'),
                                 ('Ondo', 'Ondo'), ('Osun', 'Osun'),
                                 ('Oyo', 'Oyo'), ('Plateau', 'Plateau'),
                                 ('Rivers', 'Rivers'), ('Sokoto', 'Sokoto'),
                                 ('Taraba', 'Taraba'), ('Yobe', 'Yobe'),
                                 ('Zamfara', 'Zamfara')],
                                string='State')
