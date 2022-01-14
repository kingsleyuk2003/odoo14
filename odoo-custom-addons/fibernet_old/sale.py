# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from datetime import datetime,date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class location(models.Model):
    _name = 'location'

    name = fields.Char(string='Location')
    code = fields.Char(string='Code')
    base_station_ids = fields.One2many('base.station','location_id',string='Base Station')


class BaseStation(models.Model):
    _name = 'base.station'

    name = fields.Char(string='Base Station')
    location_id = fields.Many2one('location',string='Location')

class ClientType(models.Model):
    _name = 'client.type'

    name = fields.Char(string='Name')


class SaleOrderExtend(models.Model):
    _inherit = "sale.order"

    def unlink(self):
        for order in self:
            if order.state not in ['draft','to_accept']:
                raise UserError(_('You can only delete draft quotations or Quotations Awaiting Acceptance!'))
            self.env.cr.execute("delete from sale_order where id = %s" % order.id)

    

    
    def action_confirm(self):
        self.state = 'so_to_approve'
        self.confirmed_by_user_id = self.env.user

        #Send FYI email notification
        company_email = self.env.user.company_id.email and self.env.user.company_id.email
        confirm_person_email = self.confirmed_by_user_id.partner_id.email
        confirm_person_name = self.confirmed_by_user_id.partner_id.name

        if company_email and confirm_person_email :
            # Custom Email Template
            mail_template = self.env.ref('kkon_modifications.mail_templ_quote_confirmed')
            ctx = {}
            ctx.update({'sale_id':self.id})
            the_url = self._get_sale_order_url('sale','menu_sale_order','action_orders',ctx)

            user_ids = []
            group_obj = self.env.ref('kkon_modifications.group_receive_quotation_confirmed_email')
            for user in group_obj.users:
                if user.partner_id.email and user.partner_id.email:
                    user_ids.append(user.id)
                    ctx = {
                            'system_email': company_email,
                            'confirm_person_name': confirm_person_name ,
                            'confirm_person_email' :confirm_person_email,
                            'notify_person_email': user.partner_id.email,
                            'notify_person_name': user.partner_id.name,
                            'url':the_url
                            }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)
            if user_ids:
                self.message_subscribe_users(user_ids=user_ids)

            company = self.company_id
            company_select = company.company_select

            if company_select == 'fob' or self.is_upcountry :
                # Push details to Ebilling
                self.ebilling_push_sale_info()

                #Send email for approval or disapproval
                mail_template = self.env.ref('kkon_modifications.mail_templ_quote_confirmed_to_approve')
                user_ids = []
                group_obj = self.env.ref('kkon_modifications.group_receive_quotation_confirmed_email_to_approve')
                for user in group_obj.users:
                    if user.partner_id.email and user.partner_id.email:
                        user_ids.append(user.id)
                        ctx = {
                            'system_email': company_email,
                            'confirm_person_name': confirm_person_name,
                            'confirm_person_email': confirm_person_email,
                            'notify_person_email': user.partner_id.email,
                            'notify_person_name': user.partner_id.name,
                            'url': the_url
                        }
                        mail_template.with_context(ctx).send_mail(self.id, force_send=False)
                if user_ids :
                    self.message_subscribe_users(user_ids=user_ids)

            if company_select == 'kkon':
                if not self.is_upcountry :
                    self.action_approve()

        return


    
    def action_create_payment(self, payment_date, journal_id, amount, ref, partner_id):
        account_payment_group_obj = self.env['account.payment.group']
        account_payment_obj = self.env['account.payment']

        act_pg_dict = {
            'partner_id': partner_id.id,
            'payment_date': payment_date,
            'communication': ref,
            'sale_id': self.id,
            'is_upcountry' : self.is_upcountry,
            'partner_type': 'customer',
            'company_id': self.company_id.id,

            'payment_ids': [(0, 0, {
                'payment_type': 'inbound',
                'payment_type_copy': 'inbound',
                'journal_id': journal_id.id,
                'payment_date': payment_date,
                'amount': amount,
                'communication': ref,
                'ref_no': ref,
                'payment_method_id': 1,  # Manual payment
                'partner_id': partner_id.id,
                'partner_type': 'customer',
                'company_id': self.company_id.id,
            }
                             )]
        }
        res = account_payment_group_obj.create(act_pg_dict)
        #res._refresh_payments_and_move_lines()
        # OR
        # acc_pay = {
        #     'payment_type': 'inbound',
        #     'payment_type_copy': 'inbound',
        #     'journal_id': journal_id.id,
        #     'payment_date': payment_date,
        #     'amount': amount,
        #     'ref_no': ref,
        #     'payment_method_id': 1,  # Manual payment
        #     'partner_id': partner_id.id,
        #     'partner_type': 'customer',
        #     'payment_group_id': res.id,
        # }
        # pg = account_payment_obj.create(acc_pay)
        res.post()
        res.sale_id = self
        return res


    
    def action_create_payment_entry(self):
        model_data_obj = self.env['ir.model.data']
        action = self.env['ir.model.data'].xmlid_to_object('kkon_modifications.action_create_payment')
        form_view_id = model_data_obj.xmlid_to_res_id('kkon_modifications.create_payment_wizard_view')

        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'domain': action.domain,
            'context': {'default_partner_id': self.partner_id.id,'default_total_amount_paid': self.total_amount_paid,'default_amount_balance': self.amount_balance},
            'res_model': action.res_model,
            'target': 'new'
        }


    
    def create_ticket_with_email(self):
        res = super(SaleOrderExtend, self).action_confirm()
        self.approved_by_user_id = self.env.user

        category_id = self.env.ref('kkon_modifications.kkon_installation')
        company = self.company_id
        company_select = company.company_select
        res_payment = False
        is_installation_group = False
        is_default_installation_group = False
        if company_select == 'kkon':
            is_installation_group = self.env['user.ticket.group'].search(
                [('is_installation_group_default_csc_kkon', '=', True)],limit=1)
            if not is_installation_group:
                raise UserError(_('Please contact the Administrator to set the Default Installation Group for CSC KKONTech'))
            elif is_installation_group:
                is_default_installation_group = is_installation_group.id
        elif company_select == 'fob':
            is_installation_group = self.env['user.ticket.group'].search(
                [('is_installation_group_default_csc_fob', '=', True)],limit=1)
            if not is_installation_group:
                raise UserError(_('Please contact the Administrator to set the Default Installation Group for CSC FOB'))
            elif is_installation_group:
                is_default_installation_group = is_installation_group.id

        # Create ticket
        product_order_line = self.order_line.filtered(lambda line: line.product_id.is_mrc == True)
        if product_order_line :
            product = product_order_line.product_id.id
        else:
            product = False
        vals = {
            'name': 'Installation Ticket for %s with reference as (%s) ' %  (self.name,self.client_order_ref),
            'category_id': category_id.id,
            'partner_id': self.partner_id.id,
            'location_id': self.partner_id.location_id.id,
            'base_station_id': self.partner_id.base_station_id.id,
            'ticket_company_id' : company.id,
            'initiator_ticket_group_id' : is_default_installation_group,
            'description' : ' ',
            'product_id' : product,
        }
        ticket_obj = self.env['kin.ticket'].create(vals)
        ticket_obj.order_id = self.id

        if self.is_upcountry:
            ticket_obj.is_upcountry = True

        # partn_ids = []
        # user_names = ''
        # if is_installation_group:
        #     # send group email
        #     users = is_installation_group.sudo().user_ids
        #     for user in users:
        #         if user.is_group_email:
        #             user_names += user.name + ", "
        #             partn_ids.append(user.partner_id.id)
        #
        #     if partn_ids:
        #         msg = _(
        #             'A New installation Ticket has been created for the order id - %s, from %s') % (
        #               self.name, self.env.user.name)
        #         self.message_post(
        #             msg,
        #             subject=msg, partner_ids=partn_ids,
        #             subtype_xmlid='mail.mt_comment', force_send=False)
        #         self.env.user.notify_info('%s Will Be Notified by Email for Installation Ticket Created' % (user_names))

        self.state = 'sale'
        # Send Email
        company_email = self.env.user.company_id.email
        approve_person_email = self.approved_by_user_id.partner_id.email
        approve_person_name = self.approved_by_user_id.name

        if company_email and approve_person_email:
            # Custom Email Template
            mail_template = self.env.ref('kkon_modifications.mail_templ_sale_approved')
            ctx = {}
            ctx.update({'sale_id': self.id})
            the_url = self._get_sale_order_url('sale', 'menu_sale_order', 'action_orders', ctx)

            user_ids = []
            group_obj = self.env.ref('kkon_modifications.group_receive_approve_sale_order_email')
            for user in group_obj.users:
                if user.partner_id.email and user.partner_id.email:
                    user_ids.append(user.id)
                    ctx = {'system_email': company_email,
                           'approve_person_name': approve_person_name,
                           'approve_person_email': approve_person_email,
                           'notify_person_email': user.partner_id.email,
                           'notify_person_name': user.partner_id.name,
                           'url': the_url
                           }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)
            if user_ids :
                self.message_subscribe_users(user_ids=user_ids)
        return res

    
    def action_approve(self):
        res = False
        company = self.company_id
        company_select = company.company_select
        if company_select == 'kkon':
            if self.is_upcountry :
                return self.action_create_payment_entry()
            else:
                res = self.create_ticket_with_email()
        elif company_select == 'fob' :
            # Post payment wizard
            return self.action_create_payment_entry()
        return res

    
    def action_disapprove(self, msg):
        reason_for_dispproval = msg
        self.disapproved_by_user_id = self.env.user
        self.state = 'no_sale'

        # Send Email
        company_email = self.env.user.company_id.email
        disapprove_person_email = self.disapproved_by_user_id.partner_id.email
        disapprove_person_name = self.disapproved_by_user_id.name

        if company_email and disapprove_person_email:
            # Custom Email Template
            mail_template = self.env.ref('kkon_modifications.mail_templ_sale_disapproved')
            ctx = {}
            ctx.update({'sale_id': self.id})
            the_url = self._get_sale_order_url('sale', 'menu_sale_order', 'action_orders', ctx)

            user_ids = []
            group_obj = self.env.ref('kkon_modifications.group_receive_disapprove_sale_order_email')
            for user in group_obj.users:
                if user.partner_id.email and user.partner_id.email:
                    user_ids.append(user.id)
                    ctx = {'system_email': company_email,
                           'disapprove_person_name': disapprove_person_name,
                           'disapprove_person_email': disapprove_person_email,
                           'notify_person_email': user.partner_id.email,
                           'notify_person_name': user.partner_id.name,
                           'url': the_url,
                           'reason_for_dispproval': reason_for_dispproval,
                           }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)

            if user_ids:
                self.message_subscribe_users(user_ids=user_ids)
                # For Similar Odoo Kind of Email. Works fine
                # self.message_post( _("Sales Order has been Disapproved with reason: " + reason_for_dispproval + "") ,subject='Please See the Disapproved Sales Order', subtype_xmlid='mail.mt_comment', force_send=False)

                # Just Log the Note Only
                self.message_post(_("Sales Order has been Disapproved with reason: " + reason_for_dispproval + ""),
                                  subject='Please See the Disapproved Sales Order')


    
    def action_cancel(self):
        res = super(SaleOrderExtend,self).action_cancel()

        for ticket in self.ticket_ids:
            ticket.unlink()
        self.is_installation_ticket_close = False
        self.is_free_installation = False

        if self.payment_group_ids :
            self.payment_group_ids.cancel()
            self.payment_group_ids.unlink()

        #Send Email
        company_email = self.env.user.company_id.email
        sales_person_email = self.user_id.partner_id.email
        confirm_person_email = self.env.user.partner_id.email

        if company_email and sales_person_email and confirm_person_email and  (sales_person_email != confirm_person_email ):
            # Custom Email Template
            mail_template = self.env.ref('kkon_modifications.mail_templ_sale_canceled')
            ctx = {}
            ctx.update({'sale_id':self.id})
            the_url = self._get_sale_order_url('sale','menu_sale_order','action_orders',ctx)

            ctx = {'system_email': company_email,
                    'confirm_person_name': self.env.user.name ,
                    'confirm_person_email' :confirm_person_email,
                    'url':the_url
                    }
            mail_template.with_context(ctx).send_mail(self.id,force_send=False)
        return res

    
    def write(self, vals):
        new_state = vals.get('state',False)
        if self.state == 'draft' and vals.get and new_state and new_state not in ('draft','cancel') and self.create_uid == self.env.user :
            raise UserError(_('Sorry, You cannot approve the quotation that was created by you'))
        res = super(SaleOrderExtend, self).write(vals)
        for rec in self:
            if len(rec.order_line) == 0 :
                raise UserError(_('At Least an Order Line is Required'))
        return res




    def _get_sale_order_url(self, module_name,menu_id,action_id, context=None):
        fragment = {}
        res = {}
        model_data = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fragment['menu_id'] = model_data.get_object_reference(module_name,menu_id)[1]
        fragment['model'] =  'sale.order'
        fragment['view_type'] = 'form'
        fragment['action']= model_data.get_object_reference(module_name,action_id)[1]
        query = {'db': self.env.cr.dbname}

# for displaying tree view. Remove if you want to display form view
#         fragment['page'] = '0'
#         fragment['limit'] = '80'
#         res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))


 # For displaying a single record. Remove if you want to display tree view

        fragment['id'] =  context.get("sale_id")
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
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





    # 
    # def unlink(self):
    #     for order in self:
    #         if order.state not in ['draft','to_accept']:
    #             raise UserError(_('You can only delete draft quotations, Quotations Awaiting Acceptance!'))
    #         self.env.cr.execute("delete from sale_order where id = %s" % order.id)
    #
    #         for ticket in order.ticket_ids:
    #             ticket.unlink()

    
    def btn_view_payment_groups(self):
        payment_group_ids = self.mapped('payment_group_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account_payment_group.action_account_payments_group')
        list_view_id = imd.xmlid_to_res_id('account_payment_group.view_account_payment_group_tree')
        form_view_id = imd.xmlid_to_res_id('account_payment_group.view_account_payment_group_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'target': 'new',
        }
        if len(payment_group_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % payment_group_ids.ids
        elif len(payment_group_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = payment_group_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    @api.depends('payment_group_ids')
    def _compute_payment_group_count(self):
        for rec in self:
            rec.payment_group_count = len(rec.payment_group_ids)


    @api.depends('payment_group_ids.payments_amount')
    def _compute_payment_amount(self):
        for rec in self:
            amount = 0
            if rec.payment_group_ids:
                for payment_group_id in rec.payment_group_ids:
                    amount += payment_group_id.payments_amount
                rec.total_amount_paid = amount

                if rec.amount_total != amount:
                    rec.show_alert_box_kkon = True
                    rec.amount_balance = rec.amount_total - amount
            else:
                rec.total_amount_paid = 0
                rec.amount_balance = 0
                rec.alert_msg = ''
                rec.show_alert_box_kkon = False


    ticket_ids = fields.One2many('kin.ticket', 'order_id', string='Tickets')
    ticket_count = fields.Integer(compute="_compute_ticket_count", string='# of Ticket', copy=False, default=0)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        # ('advance', 'Cash Sales'),
        # ('credit', 'Credit Sales'),
        ('so_to_approve', 'Sale Order To Approve'),
        ('sale', 'Sale Order Approved'),
        ('no_sale', 'Sale Order Disapproved'),
        ('credit_limit_by_pass_request', 'Credit Limit By Pass Request'),
        ('credit_limit_by_pass_confirm', 'Credit Limit By Pass Confirmed'),
        ('credit_limit_by_pass_approve', 'Credit Limit By Pass Approved'),
        ('credit_limit_by_pass_disapprove', 'Credit Limit By Pass DisApproved'),
        ('credit_limit_by_pass_cancel', 'Credit Limit By Pass Cancelled'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')

    is_installation_ticket_close = fields.Boolean(string='Installation Ticket Closed')
    is_free_installation = fields.Boolean(string='Free Installation')
    confirmed_by_user_id = fields.Many2one('res.users', string='Confirmed By')
    approved_by_user_id = fields.Many2one('res.users', string='Approved By')
    disapproved_by_user_id = fields.Many2one('res.users', string='Disapproved By')
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
                                 states={'draft': [('readonly', False), ('required', False)],
                                         'sent': [('readonly', False)], 'waiting': [('readonly', False)],
                                         'so_to_approve': [('readonly', False)]}, copy=False)
    street = fields.Char(related='partner_id.street', string='Address')
    phone = fields.Char(related='partner_id.phone', string='Phone')
    email = fields.Char(related='partner_id.email', string='Email')
    payment_group_id = fields.Many2one('account.payment.group',string='Payment')
    payment_group_ids = fields.One2many('account.payment.group','sale_id',string='Payments')
    total_amount_paid = fields.Monetary(string='Total Amount Paid', compute='_compute_payment_amount', store=True)
    amount_balance = fields.Monetary(string='Balance to be Paid', compute='_compute_payment_amount', store=True)
    show_alert_box_kkon = fields.Boolean(string="Show Alert Box")
    alert_msg = fields.Char(string='Alert Message')
    payment_group_count = fields.Integer(compute="_compute_payment_group_count", string='# of Payment Groups', copy=False, default=0)
    ebilling_order_push = fields.Boolean(string='Ebilling Order Pushed')
    ebilling_order_response = fields.Char(string='Ebilling Order Response')
    is_successful_ebilling_payment_receipt = fields.Boolean(string='Ebilling Payment Receipt Successful')
    ebilling_payment_receipt_error_msg = fields.Char(string='Ebilling Payment Receipt Error Message')
    ebilling_order_manually_approved_pushed = fields.Boolean(string='Ebilling Order Manually Approved Pushed')
    is_upcountry = fields.Boolean(string='Up Country Transaction')

class ResPartnerExtend(models.Model):
    _inherit = 'res.partner'

    def create(self, vals):
        customer_type = vals.get('customer_type',False)
        is_parent_id = vals.get('parent_id',False)
        is_upcountry = vals.get('is_upcountry',False)
        if not is_parent_id and customer_type  and customer_type == 'kkon':
            if is_upcountry:
                vals['ref'] = self.env['ir.sequence'].next_by_code('fob_code')
            else:
                vals['ref'] = self.env['ir.sequence'].next_by_code('kkon_code')
        elif not is_parent_id and customer_type and customer_type == 'fob':
            vals['ref'] = self.env['ir.sequence'].next_by_code('fob_code')
        elif not is_parent_id and customer_type and customer_type == 'reseller':
            vals['ref'] = self.env['ir.sequence'].next_by_code('res_code')
        elif not is_parent_id and customer_type and customer_type == 'carrier':
            vals['ref'] = self.env['ir.sequence'].next_by_code('carr_code')

        res = super(ResPartnerExtend,self).create(vals)

        if not is_parent_id and customer_type:
            if customer_type == 'fob' or res.is_upcountry or customer_type == 'reseller':
                import requests
                headers = {'AUTHORIZATION': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpZCI6ImVycCIsImVudHJ5Ijoid2Vic2VydmljZSEyMyJ9.bcQ8DXROZY-G1lVgEaU1hpz4WQxaZaOffJZEglJnCf8vCgxWAE7GSiBh_9BhHmcMW3h3hgw9DrQzV5h17DwUfw'}
                payload = {'erpid': res.id,
                           'username': res.ref or '',
                           'company': res.name or '',
                           'address': res.street or '',
                           'email': res.email or '',
                           'phone': res.phone or '',
                           'mobile': res.mobile or '',
                           'ip': res.ip_address or '',
                           'pck': res.product_id and res.product_id.name or '',
                           'company_id' : res.company_id.id,
                           'title' : res.title and res.title.name or '',
                           'first_name' : res.first_name or '',
                           'last_name' : res.last_name or '',
                           'gender' : res.gender or '',
                           'estate' : res.estate_id and res.estate_id.name or '',
                           'city_cust' : res.city_cust or '',
                           'dob' : res.dob or '',
                           'expiration': res.expiration or '',
                           'reg_date' : res.reg_date or '',
                           'last_logoff' : res.last_logoff or '',
                           'gpon' : res.gpon or '',
                           'interface' : res.interface or '',
                           'serial_no' : res.serial_no or '',
                           'state_ng' : res.state_ng or '',
                           }
                try:
                    response = requests.post("https://eservice.fob.ng/apy/public/erp/user", verify=True,  data=payload, headers=headers)
                    if response.status_code != requests.codes.ok:
                        raise UserError(_('Sorry, There is an issue creating the customer on the external EBILLING application '))
                    else:
                        res.env.cr.execute("update res_partner set ebilling_push = True, ebilling_response = '%s' where id = %s" % (response.text,res.id))
                except Exception, e:
                    import logging
                    _logger = logging.getLogger(__name__)
                    _logger.exception(e)
                    raise UserError(_('Sorry, ODEX ERP cannot connect with EBILLING service. Please contact your IT Administrator. Eservice message: %s' % (e)))

        return res

    
    def write(self, vals):
        res = super(ResPartnerExtend, self).write(vals)
        for rec in self:
            customer_type = rec.customer_type
            is_parent_id = rec.parent_id
            client_id = rec.ref
            if not is_parent_id and not client_id and customer_type and customer_type == 'kkon':
                if self.is_upcountry :
                    rec.ref = self.env['ir.sequence'].next_by_code('fob_code')
                else:
                    rec.ref = self.env['ir.sequence'].next_by_code('kkon_code')
            elif not is_parent_id and not client_id and customer_type and customer_type == 'fob':
                rec.ref = self.env['ir.sequence'].next_by_code('fob_code')
            elif not is_parent_id and not client_id and customer_type and customer_type == 'reseller':
                rec.ref = self.env['ir.sequence'].next_by_code('res_code')
            elif not is_parent_id and not client_id and customer_type and customer_type == 'carrier':
                rec.ref = self.env['ir.sequence'].next_by_code('carr_code')

            if not is_parent_id and not rec.ref and customer_type:
                if customer_type == 'fob' or self.is_upcountry or customer_type == 'reseller':
                    import requests
                    headers = {
                        'AUTHORIZATION': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpZCI6ImVycCIsImVudHJ5Ijoid2Vic2VydmljZSEyMyJ9.bcQ8DXROZY-G1lVgEaU1hpz4WQxaZaOffJZEglJnCf8vCgxWAE7GSiBh_9BhHmcMW3h3hgw9DrQzV5h17DwUfw'}
                    payload = {'erpid': self.id,
                               # 'firstname': 'Testuser1',
                               # 'lastname': 'testLastname',
                               'username': self.ref or '',
                               'company': self.name or '',
                               'address': self.street or '',
                               # 'state': 'Oyo',
                               'email': self.email or '',
                               'phone': self.phone or '',
                               'mobile': self.mobile or '',
                               'ip': self.ip_address or '',
                               'pck': self.product_id and self.product_id.name or '',
                               'company_id': self.company_id.id,
                            'title' : self.title and self.title.name or '',
                           'first_name' : self.first_name or '',
                           'last_name' : self.last_name or '',
                           'gender' : self.gender or '',
                           'estate' : self.estate_id and self.estate_id.name or '',
                           'city_cust' : self.city_cust or '',
                           'dob' : self.dob or '',
                           'expiration': self.expiration or '',
                           'reg_date' : self.reg_date or '',
                           'last_logoff' : self.last_logoff or '',
                           'gpon' : self.gpon or '',
                           'interface' : self.interface or '',
                           'serial_no' : self.serial_no or '',
                           'state_ng' : self.state_ng or '',
                               }
                    try:
                        response = requests.post("https://eservice.fob.ng/apy/public/erp/user", verify=True, data=payload,
                                                 headers=headers)
                        if response.status_code != requests.codes.ok:
                            raise UserError(
                                _('Sorry, There is an issue creating the customer on the external EBILLING application '))
                        else:
                            self.env.cr.execute("update res_partner set ebilling_push = True, ebilling_response = '%s' where id = %s" % (response.text,rec.id))
                    except Exception, e:
                        import logging
                        _logger = logging.getLogger(__name__)
                        _logger.exception(e)
                        raise UserError(
                            _('Sorry, ODEX ERP cannot connect with EBILLING service. Please contact your IT Administrator, with error: %s' % (e)))

        return res

    
    def btn_push_customer_ebilling(self):
        if not self.parent_id and self.customer_type:
            if self.customer_type == 'fob' or self.is_upcountry or self.customer_type == 'reseller':
                import requests
                headers = {
                    'AUTHORIZATION': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpZCI6ImVycCIsImVudHJ5Ijoid2Vic2VydmljZSEyMyJ9.bcQ8DXROZY-G1lVgEaU1hpz4WQxaZaOffJZEglJnCf8vCgxWAE7GSiBh_9BhHmcMW3h3hgw9DrQzV5h17DwUfw'}
                payload = {'erpid': self.id,
                           # 'firstname': 'Testuser1',
                           # 'lastname': 'testLastname',
                           'username': self.ref or '',
                           'company': self.name or '',
                           'address': self.street or '',
                           # 'state': 'Oyo',
                           'email': self.email or '',
                           'phone': self.phone or '',
                           'mobile': self.mobile or '',
                           'ip': self.ip_address or '',
                           'pck': self.product_id and self.product_id.name or '',
                           'company_id': self.company_id.id,
                           
                           'title' : self.title and self.title.name or '',
                           'first_name' : self.first_name or '',
                           'last_name' : self.last_name or '',
                           'gender' : self.gender or '',
                           'estate' : self.estate_id and self.estate_id.name or '',
                           'city_cust' : self.city_cust or '',
                           'dob' : self.dob or '',
                           'expiration': self.expiration or '',
                           'reg_date' : self.reg_date or '',
                           'last_logoff' : self.last_logoff or '',
                           'gpon' : self.gpon or '',
                           'interface' : self.interface or '',
                           'serial_no' : self.serial_no or '',
                           'state_ng' : self.state_ng or '',
                           }
                try:
                    response = requests.post("https://eservice.fob.ng/apy/public/erp/user", verify=True, data=payload, headers=headers)
                    if response.status_code != requests.codes.ok:
                        raise UserError(
                            _('Sorry, There is an issue creating the customer on the external EBILLING application '))
                    else:
                        self.env.cr.execute("update res_partner set ebilling_push = True, ebilling_response = '%s' where id = %s" % (response.text,self.id))
                        # send email
                        user_ids = []
                        group_obj = self.env.ref('kkon_modifications.group_push_ebilling_customer')
                        user_names = ''
                        for user in group_obj.sudo().users:
                            user_names += user.name + ", "
                            user_ids.append(user.partner_id.id)
                        self.message_post(
                            _(
                                '%s has Re-Pushed an existing Customer (%s) to the Ebilling Service') % (
                                self.env.user.name,self.name ),
                            subject='Existing Customer Re-Pushed', partner_ids=user_ids, subtype_xmlid='mail.mt_comment', force_send=False)
                        self.env.user.notify_info('%s Will Be Notified by Email for Re-Pushing an Existing Customer' % (user_names))

                except Exception, e:
                        import logging
                        _logger = logging.getLogger(__name__)
                        _logger.exception(e)
                        raise UserError(
                            _('Sorry, ODEX ERP cannot connect with EBILLING service. Please contact your IT Administrator, with error: %s' % (e)))



    #product_ids = fields.Many2many('product.product', string='Package(s)')
    product_id = fields.Many2one('product.product', string='Package')
    location_id = fields.Many2one('kkon.location',string='Location')
    base_station_id = fields.Many2one('base.station',string='Base Station')
    client_type_id  = fields.Many2one('client.type',string='Client Type')
    bandwidth = fields.Char(string='Bandwidth')
    contact_person = fields.Char(string='Contact Person')
    cpe = fields.Char('CPE Model')
    ip_address = fields.Char(string='Customer IP Address')
    radio_ip_address = fields.Char(string='Radio IP Address')
    base_station_ip_address = fields.Char(string='Base Station IP Address')
    subnet = fields.Char(string='Subnet')
    gateway = fields.Char(string='Gateway')
    indoor_wan = fields.Char(string='Indoor WAN IP Address')
    vlan = fields.Char(string='Vlan')
    olt_id = fields.Many2one('kkon.olt', string='OLT')
    region_id = fields.Many2one('kkon.region', string='Region')
    estate_id = fields.Many2one('kkon.estate', string='Estate')
    area_id = fields.Many2one('kkon.area',string='Area')

    comment = fields.Char(string='Comment')
    installation_date = fields.Date(string='Installation Date')
    config_status = fields.Char(string='Configuration Status')
    customer_type = fields.Selection([
        ('kkon', 'KKONTECH'),
        ('fob', 'FOB'),
        ('reseller','RESELLER'),
        ('carrier','CARRIER'),
        ('supplier', 'SUPPLIER'),
        ('employee', 'EMPLOYEE')
    ], string='Customer/Partner Type')
    active_cust = fields.Selection([
        ('Yes', 'Yes'),
        ('No', 'No')
    ], string='Active')
    ebilling_push = fields.Boolean(string='Ebilling Pushed')
    ebilling_response = fields.Char(string='Ebilling Response')
    is_upcountry = fields.Boolean(string='Is Upcountry Customer')

    first_name  = fields.Char(string="First Name")
    last_name  = fields.Char(string="Last Name")
    gender = fields.Selection([('male','Male'),('female','Female'),('not_set','Not Set')], string='Gender')

    city_cust = fields.Char(string='City')
    dob = fields.Date(string="DOB")
    expiration = fields.Date(string="Expiration")
    reg_date = fields.Date(string="REG Date")
    last_logoff = fields.Date(string="Last Logoff")
    gpon = fields.Char(string="GPON")
    interface = fields.Char(string="Interface")
    serial_no = fields.Char(string="Serial No")
    state_ng = fields.Selection([
        ('Abia', 'Abia'),
        ('FCT', 'Abuja Federal Capital Territory'),
        ('Adamawa', 'Adamawa'),
        ('Akwa Ibom','Akwa Ibom'),
        ('Anambra','Anambra'),
        ('Bauchi', 'Bauchi'),
        ('Bayelsa', 'Bayelsa'),
         ('Benue','Benue'),
        ('Borno','Borno'),
        ('Cross River', 'Cross River'),
        ('Delta', 'Delta'),
        ('Ebonyi','Ebonyi'),
        ('Edo','Edo'),
        ('Ekiti', 'Ekiti'),
        ('Enugu', 'Enugu'),
        ('Gombe','Gombe'),
        ('Imo','Imo'),
        ('Jigawa', 'Jigawa'),
        ('Kaduna', 'Kaduna'),
        ('Kano','Kano'),
        ('Katsina','Katsina'),
         ('Kebbi', 'Kebbi'),
        ('Kogi', 'Kogi'),
        ('Kwara','Kwara'),
        ('Lagos','Lagos'),
        ('Nasarawa', 'Nasarawa'),
        ('Niger', 'Niger'),
        ('Ogun','Ogun'),
        ('Ondo','Ondo'),
        ('Osun', 'Osun'),
        ('Oyo', 'Oyo'),
        ('Plateau','Plateau'),
        ('Rivers','Rivers'),
        ('Sokoto', 'Sokoto'),
        ('Taraba', 'Taraba'),
        ('Yobe','Yobe'),
        ('Zamfara','Zamfara'),
        ('not_set','Not Set')         
    ], string='State')







class ResCompany(models.Model):
    _inherit = "res.company"

    is_send_email_expiry_finish = fields.Boolean(string='Send Email Notification for Expired Tickets', default=True)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    sale_id = fields.Many2one('sale.order', string='Sales Order')