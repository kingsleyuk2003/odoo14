# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from datetime import datetime, timedelta
from odoo import SUPERUSER_ID
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from urllib.parse import urlencode
from urllib.parse import urljoin
import  time

class CRMStage(models.Model):
    _inherit = 'crm.stage'

    is_create_customer = fields.Boolean(string='Create Customer')


class CRMActivity(models.Model):
    _inherit = 'crm.activity.report'

    stage_id = fields.Many2one('crm.stage',string='Stage')


class CRMProductLine(models.Model):
    _name = 'crm.product.line'


    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.category_id.id != self.product_uom.category_id.id):
            self.product_uom = self.product_id.uom_id

        product = self.product_id.with_context(
            quantity=self.product_uom_qty,
            uom=self.product_uom.id,
        )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        self.name = name
        self.price_unit = product.list_price
        self.tax_id = product.taxes_id


    @api.depends('price_subtotal', 'product_uom_qty')
    def _get_price_reduce(self):
        for line in self:
            line.price_reduce = line.price_subtotal / line.product_uom_qty if line.product_uom_qty else 0.0


    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, self.env.user.company_id.currency_id, line.product_uom_qty, product=line.product_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=True)
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Monetary(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.user.company_id.currency_id,
                                  related='lead_id.currency_id', store=True, ondelete='restrict')

    lead_id = fields.Many2one('crm.lead', string='CRM Lead', required=True, ondelete='cascade', index=True, copy=False)
    company_id = fields.Many2one('res.company', 'Company', related='lead_id.company_id')

class CrmLeadExtend(models.Model):
    _inherit = 'crm.lead'

    def button_dummy(self):
        return True

    def action_quotation_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        if not self.email_from:
            raise UserError('Please set the Email on the form')
        if not self.contact_name :
            raise UserError('Please set the Contact Name on the form')
        template = self.env.ref('kin_crm.email_template_crm', False)
        lang = self.env.context.get('lang')
        if template.lang:
            lang = template._render_lang([self.id])[self.id]
        ctx = {
            'default_model': 'crm.lead',
            'default_res_id': self.id,
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }


    def action_create_customer(self):
        if not self.partner_id:
            partner_obj = self.env['res.partner'].create({
                'name' : self.partner_name or self.contact_name,
                'street': self.street or '',
                'email': self.email_from or '',
                'phone' : self.phone or '',
                'mobile' : self.mobile or '',
                'type' : 'contact',
            })
            self.partner_id = partner_obj

            # notify responsible people
            partn_ids = []
            group_obj = self.env.ref('kin_crm.group_receive_new_customer_from_lead')
            user_names = ''
            for user in group_obj.users:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)
            if partn_ids:
                self.message_follower_ids.unlink()
                self.message_post(body=_('A New Customer (%s) has been created for the CRM Opportunity with id - %s, from %s') % (partner_obj.name, self.name, self.env.user.name), subject='A Customer has been created', partner_ids=partn_ids, subtype_xmlid='mail.mt_comment',
                                  force_send=False)
                self.env.user.notify_info('%s Will Be Notified by Email for Customer Created' % (user_names))

            return partner_obj


    #
    # def action_set_won(self):
    #     res = super(CrmLeadExtend,self).action_set_won()
    #
    #     if self.stage_id.is_create_customer:
    #         partner_id = self.action_create_customer()
    #
    #     return res


    def _get_url(self, module_name, menu_id, action_id, context=None):
        fragment = {}
        res = {}
        model_data = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fragment['menu_id'] = model_data.get_object_reference(module_name, menu_id)[1]
        fragment['model'] = 'crm.lead'
        fragment['view_type'] = 'form'
        fragment['action'] = model_data.get_object_reference(module_name, action_id)[1]
        query = {'db': self.env.cr.dbname}

        # for displaying tree view. Remove if you want to display form view
        #         fragment['page'] = '0'
        #         fragment['limit'] = '80'
        #         res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))


        # For displaying a single record. Remove if you want to display tree view

        fragment['id'] = context.get("opp_id")
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res


    def create_quotation(self):
        if not self.order_ids :
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            partner_id = self.partner_id or False

            opportunity = self
            if not opportunity.product_line_ids :
                raise UserError(_('Please enter at least one product line'))

            order_lines = []
            for product_line_id in opportunity.product_line_ids :
                product_uom_qty =  product_line_id.product_uom_qty

                if product_uom_qty == 0 :
                    raise UserError(_('Sorry, No product Qty has been Set'))

                if not float_is_zero(product_uom_qty, precision_digits=precision):
                    order_lines += [(0, 0, {
                        'name':  product_line_id.product_id.name,
                        'product_id': product_line_id.product_id.id,
                        'discount': product_line_id.discount,
                        'product_uom_qty': product_line_id.product_uom_qty,
                        'product_uom': product_line_id.product_uom.id,
                        'price_unit': product_line_id.price_unit,
                        'tax_id' : product_line_id.tax_id,
                    })
                    ]
            if order_lines:
                #create the Quotation
                order_id = self.env['sale.order'].create({
                        'sale_order_template_id' : self.sale_order_template_id and self.sale_order_template_id.id or False,
                          'date_order' : datetime.today(),
                          'partner_id': self.partner_id.id,
                            'partner_invoice_id': self.partner_id.id,
                            'partner_shipping_id': self.partner_id.id,
                            'opportunity_id' :  self.id,
                            # 'pricelist_id': self.pricelist_id.id,
                            'client_order_ref': self.name,
                            'order_line': order_lines,
                        })
                # Notify people
                partn_ids = []
                user_names = ''
                group_obj = self.env.ref('kin_crm.group_notify_new_quote_opportunity')
                for user in group_obj.users:
                    partn_ids.append(user.partner_id.id)
                    user_names += user.name + ", "

                    if partn_ids:
                        self.message_follower_ids.unlink()
                        self.message_post(body=_('A New Quotation has been created by %s, from the Opportunity - %s, for customer %s') % (self.env.user.name, self.name,self.partner_id.name), subject='A New Quotation from Opportunities has been Created', partner_ids=partn_ids,
                                          subtype_xmlid='mail.mt_comment', force_send=False)
                        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

                return order_id




    def write(self, vals):
        #send email to sales person
        sales_person = self.user_id
        activity_id = vals.get('next_activity_id',False)
        task_title = vals.get('title_action','')
        task_date = vals.get('date_action',False)
        # company_email = sales_person.company_id.email.strip()
        task_date_format = 'Any Time'
        if task_date :
            task_date_format = task_date
        if sales_person.email and sales_person.email.strip() and activity_id:
            mail_template = self.env.ref('kin_crm.mail_templ_next_activity_created')
            ctx = {}
            ctx.update({'opp_id': self.id})
            the_url = self._get_url('crm', 'crm_lead_menu_activities', 'crm_lead_action_activities', ctx)

            ctx = {'system_email': sales_person.partner_id.email,
                    'sales_person_email': sales_person.partner_id.email,
                    'sales_person_name': sales_person.partner_id.name,
                    'url': the_url,
                    'opp_name': self.name,
                    'task_title' : task_title,
                    'task_date':task_date_format,
                    'next_activity_type': self.env['crm.activity'].browse(activity_id).name
                 }
            mail_template.with_context(ctx).send_mail(self.id, force_send=False)

        company_id = self.company_id
        is_create_quote_on_won = self.env['ir.config_parameter'].sudo().get_param('kin_crm.is_create_quote_on_won',default=False)
        #check if it is a won stage
        stage_id = vals.get('stage_id',False)
        if stage_id :
            stage = self.env['crm.stage'].browse(stage_id)
            if stage.is_create_customer and stage.is_won == True:
                self.date_won = datetime.today()
                self.action_create_customer()
                # create quotation
                if not company_id:
                    raise UserError(_('Please set the company field on the opportunity page'))
                if company_id:
                    if not self.partner_id:
                        raise UserError(_('Please set a customer to create a quotation'))
                    if is_create_quote_on_won:
                        self.create_quotation()
            elif not stage.is_create_customer and not is_create_quote_on_won and stage.is_won == True:
                self.date_won = datetime.today()
            elif not stage.is_create_customer and is_create_quote_on_won  and stage.is_won == True :
                raise UserError(_('Please contact the Admin to set the "Create Customer" on the WON stages'))
            else:
                self.date_won = False

        return super(CrmLeadExtend,self).write(vals)



    def cancel_next_activity(self):
        # send email to sales person
        sales_person = self.user_id
        activity_id = self.next_activity_id
        task_title = self.title_action
        task_date = self.date_action
        company_email = self.env.user.company_id.email.strip()
        task_date_format = 'Any Time'
        if task_date:
            task_date_format = datetime.strptime(task_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        if sales_person.email and sales_person.email.strip() and activity_id:
            mail_template = self.env.ref('kin_crm.mail_templ_cancel_activity_created')
            ctx = {}
            ctx.update({'opp_id': self.id})
            the_url = self._get_url('crm', 'crm_lead_menu_activities', 'crm_lead_action_activities', ctx)

            ctx = {'system_email': company_email,
                   'sales_person_email': sales_person.partner_id.email,
                   'sales_person_name': sales_person.partner_id.name,
                   'url': the_url,
                   'opp_name': self.name,
                   'task_title': task_title,
                   'task_date': task_date_format,
                   'next_activity_type': activity_id.name
                   }
            mail_template.with_context(ctx).send_mail(self.id, force_send=False)
        return super(CrmLeadExtend,self).cancel_next_activity()


    def log_next_activity_done(self,next_activity_name=False):
        #change the state of the stage if any link
        if self.next_activity_id.stage_id :
            self.stage_id = self.next_activity_id.stage_id

            #send email to the sales manager
        sales_person = self.user_id
        activity_id = self.next_activity_id
        task_title = self.title_action
        task_date = self.date_action
        company_email = self.env.user.company_id.email.strip()
        task_date_format = 'Any Time'
        if task_date:
            task_date_format = datetime.strptime(task_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        if sales_person and self.team_id and self.team_id.user_id and self.team_id.user_id.email and self.team_id.user_id.email.strip() and activity_id:
            mail_template = self.env.ref('kin_crm.mail_templ_done_activity_created')
            ctx = {}
            ctx.update({'opp_id': self.id})
            sales_manager = self.team_id.user_id
            the_url = self._get_url('crm', 'crm_lead_menu_activities', 'crm_lead_action_activities', ctx)

            ctx = {'system_email': company_email,
                   'sales_manager_email': sales_person.partner_id.email,
                   'sales_person_name': sales_person.partner_id.name,
                   'sales_manager_email': sales_manager.partner_id.email,
                   'sales_person_name': sales_manager.partner_id.name,
                   'url': the_url,
                   'opp_name': self.name,
                   'task_title': task_title,
                   'task_date': task_date_format,
                   'next_activity_type': activity_id.name
                   }
            mail_template.with_context(ctx).send_mail(self.id, force_send=False)

        return super(CrmLeadExtend, self).log_next_activity_done(next_activity_name=next_activity_name)


    @api.depends('product_line_ids.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for lead in self:
            amount_untaxed = amount_tax = 0.0
            for line in lead.product_line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                lead.update({
                'amount_untaxed': lead.currency_id.round(amount_untaxed),
                'amount_tax': lead.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
                'expected_revenue' : lead.currency_id.round(amount_untaxed),
                })

    def _compute_line_data_for_template_change(self, line):
        return {
            'name': line.name,
        }



    @api.onchange('sale_order_template_id')
    def onchange_sale_order_template_id(self):
        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)
        # --- first, process the list of products from the template
        order_lines = [(5, 0, 0)]
        for line in template.sale_order_template_line_ids:
            data = self._compute_line_data_for_template_change(line)
            if line.product_id:
                discount = 0
                data.update({
                    'price_unit': line.amount,
                    'discount': discount,
                    'product_uom_qty': line.product_uom_qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'tax_id': line.tax_ids,
                })

            order_lines.append((0, 0, data))

        self.product_line_ids = order_lines

        if template.note:
            self.note = template.note



    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id, ondelete='restrict')
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all',
                                 track_visibility='always')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always')
    note = fields.Text('Note')
    date_won = fields.Date(string='Date Won')

    product_line_ids = fields.One2many('crm.product.line', 'lead_id', string='Product Lines', copy=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('sale.order'))

    sale_order_template_id = fields.Many2one(
        'sale.order.template', 'Quotation Template', check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")



class CRMUserTarget(models.Model):
    _name = 'crm.user.target'
    _order = 'start_date asc'

    @api.depends('target_opportunity')
    def _amount_all(self):
        for rec in self :
            start_date = rec.start_date
            end_date = rec.end_date
            opportunity_target = rec.target_opportunity
            actual_won_opportunity_revenue = 0
            perc_opportunity_target_won = 0

            crm_lead_obj = rec.env['crm.lead'].search(
                    [('stage_id.is_won', '=', True), ('date_won', '>=', start_date), ('date_won', '<=', end_date),
                     ('user_id', '=', rec.user_id.id)])
            total_amount_untaxed = 0
            for crm_lead in crm_lead_obj:
                total_amount_untaxed += crm_lead.amount_untaxed

                actual_won_opportunity_revenue = total_amount_untaxed
                if opportunity_target:
                    perc_opportunity_target_won = (actual_won_opportunity_revenue / opportunity_target) * 100
                else:
                    perc_opportunity_target_won = 0
            rec.update({
                'actual_won_opportunity_revenue': actual_won_opportunity_revenue,
                'perc_opportunity_target_won': perc_opportunity_target_won,
             })

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    user_id = fields.Many2one('res.users',string='User')
    target_opportunity = fields.Float(string='Target Opportunity')
    actual_won_opportunity_revenue = fields.Float(string='Won Opportunity Revenue',compute='_amount_all')
    perc_opportunity_target_won = fields.Float(string='Percentage of Won Opportunity Target (%)',compute='_amount_all')
    crm_target_opportunity_id = fields.Many2one('crm.target.opportunity', string='CRM Target Opportunity')
    company_id = fields.Many2one('res.company',string='Company')


class CRMTargetOpportunity(models.Model):
    _name = 'crm.target.opportunity'



    def btn_target_compute(self):
        start_date = self.start_date
        end_date = self.end_date
        sales_team = self.sales_team
        total_opportunity_target = 0
        total_actual_won_opportunity_revenue = 0
        total_perc_opportunity_target_won = 0
        self.target_lines_ids.unlink()

        for member in sales_team.member_ids:
            crm_lead_obj = self.env['crm.lead'].search([('stage_id.is_won','=',True),('date_won','>=',start_date),('date_won','<=',end_date),('user_id','=',member.id)])
            total_amount_untaxed = 0
            for crm_lead in crm_lead_obj :
                total_amount_untaxed += crm_lead.amount_untaxed

            crm_user_target_obj = self.env['crm.user.target'].search([('start_date', '>=', start_date), ('end_date', '<=', end_date),('user_id', '=', member.id)])
            opportunity_target = 0
            for crm_user_target in crm_user_target_obj:
                opportunity_target += crm_user_target.target_opportunity

            actual_won_opportunity_revenue = total_amount_untaxed
            if opportunity_target :
                perc_opportunity_target_won = (actual_won_opportunity_revenue/opportunity_target) * 100
            else:
                perc_opportunity_target_won = 0

            total_opportunity_target += opportunity_target
            total_actual_won_opportunity_revenue += actual_won_opportunity_revenue
            if total_opportunity_target :
                total_perc_opportunity_target_won = (total_actual_won_opportunity_revenue/total_opportunity_target) * 100
            else:
                total_perc_opportunity_target_won = 0

            self.env['crm.target.opportunity.lines'].create(
                {
                    'user_id': member.id,
                    'opportunity_target' : opportunity_target,
                    'actual_won_opportunity_revenue' : actual_won_opportunity_revenue,
                    'perc_opportunity_target_won': perc_opportunity_target_won,
                    'crm_target_opportunity_id': self.id
                }
            )
        self.write({'total_opportunity_target': total_opportunity_target,
                    'total_actual_won_opportunity_revenue': total_actual_won_opportunity_revenue,
                    'total_perc_opportunity_target_won': total_perc_opportunity_target_won})


    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    sales_team = fields.Many2one('crm.team',string="Team")
    target_lines_ids = fields.One2many('crm.target.opportunity.lines','crm_target_opportunity_id',string='Target Lines')
    company_id = fields.Many2one('res.company', string='Company', select=True,default=lambda self: self.env.user.company_id)
    total_opportunity_target = fields.Float(string='Total Opportunity Target')
    total_actual_won_opportunity_revenue = fields.Float(string='Total Won Opportunity Revenue')
    total_perc_opportunity_target_won = fields.Float(string='Total Percentage of Won Opportunity Target (%)')


class CRMTargetOpportunityLines(models.Model):
    _name = 'crm.target.opportunity.lines'

    user_id = fields.Many2one('res.users',string='Team Member')
    opportunity_target = fields.Float(string='Opportunity Target')
    actual_won_opportunity_revenue = fields.Float(string='Won Opportunity Revenue')
    perc_opportunity_target_won = fields.Float(string='Percentage of Won Opportunity Target (%)')
    crm_target_opportunity_id = fields.Many2one('crm.target.opportunity',string='CRM Target Opportunity')
    company_id = fields.Many2one('res.company',related='crm_target_opportunity_id.company_id' ,string='Company')
