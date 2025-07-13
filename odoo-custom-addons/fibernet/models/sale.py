# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
import base64
from builtins import super
from datetime import datetime,date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
import requests, logging, json
from odoo.tools.misc import format_amount
import urllib.parse

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

    def send_email(self, grp_name, subject, msg):
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref(grp_name)

        for user in group_obj.users:
            if user.is_group_email:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

        if partn_ids:
            # self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

    @api.onchange('sale_order_template_id')
    def onchange_sale_order_template_id(self):

        if not self.sale_order_template_id:
            self.require_signature = self._get_default_require_signature()
            self.require_payment = self._get_default_require_payment()
            return

        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)

        # --- first, process the list of products from the template
        order_lines = [(5, 0, 0)]
        for line in template.sale_order_template_line_ids:
            data = self._compute_line_data_for_template_change(line)

            if line.product_id:
                price = line.product_id.lst_price
                discount = 0

                if self.pricelist_id:
                    pricelist_price = self.pricelist_id.with_context(uom=line.product_uom_id.id).get_product_price(
                        line.product_id, 1, False)

                    if self.pricelist_id.discount_policy == 'without_discount' and price:
                        discount = max(0, (price - pricelist_price) * 100 / price)
                    else:
                        price = pricelist_price

                data.update({
                    'price_unit': line.amount,
                    'discount': discount,
                    'product_uom_qty': line.product_uom_qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'customer_lead': self._get_customer_lead(line.product_id.product_tmpl_id),
                })

            order_lines.append((0, 0, data))

        self.order_line = order_lines
        self.order_line._compute_tax_id()

        # then, process the list of optional products from the template
        option_lines = [(5, 0, 0)]
        for option in template.sale_order_template_option_ids:
            data = self._compute_option_data_for_template_change(option)
            option_lines.append((0, 0, data))

        self.sale_order_option_ids = option_lines

        if template.number_of_days > 0:
            self.validity_date = fields.Date.context_today(self) + timedelta(template.number_of_days)

        self.require_signature = template.require_signature
        self.require_payment = template.require_payment

        if template.note:
            self.note = template.note

    @api.onchange('client_type')
    def onchange_client_type(self):
        self.sale_order_template_id = False

    def unlink(self):
        for order in self:
            if order.state not in ['draft','to_accept']:
                raise UserError(_('You can only delete draft quotations or Quotations Awaiting Acceptance!'))
            self.env.cr.execute("delete from sale_order where id = %s" % order.id)

    
    def action_confirm(self):
        self.state = 'so_to_approve'
        self.confirmed_by_user_id = self.env.user

        if self.partner_id.ref :
            raise UserError('Sorry, this is not a new customer. You can create a new customer for a new installation')

        grp_name = 'fibernet.group_receive_quotation_confirmed_email_to_approve'
        subject = 'A New Sales Quote has been Submitted'
        msg = _('The Sales Order %s by %s, requires your approval') % (
            self.name, self.env.user.name)
        self.send_email(grp_name, subject, msg)

        return


    
    def action_create_payment(self, payment_date, journal_id, amount, ref, partner_id):
        account_payment_obj = self.env['account.payment']
        act_pg_dict = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': partner_id.id,
                'amount': amount,
                'date': payment_date,
                'ref': ref,
                'journal_id': journal_id.id,
            }
        res = account_payment_obj.create(act_pg_dict)
        res.action_post()
        res.sale_id = self
        return res

    # def get_payment_type(self):
    #     is_paid_deferred = False
    #     product_subscription_line = self.order_line.filtered(lambda line: line.product_id.is_sub == True)
    #     if product_subscription_line:
    #         is_paid_deferred = "paid"
    #     else:
    #         is_paid_deferred = "deferred"
    #     return is_paid_deferred


    def action_create_payment_entry(self):
        model_data_obj = self.env['ir.model.data']
        action = self.env['ir.model.data'].xmlid_to_object('fibernet.action_create_payment')
        form_view_id = model_data_obj.xmlid_to_res_id('fibernet.create_payment_wizard_view')

        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'domain': action.domain,
            'context': {'default_partner_id': self.partner_id.id,'default_total_amount_paid': self.total_amount_paid,'default_amount_balance': self.amount_balance or self.amount_total},
            'res_model': action.res_model,
            'target': 'new'
        }


    
    def create_ticket_with_email(self):
        res = super(SaleOrderExtend, self).action_confirm()
        self.approved_by_user_id = self.env.user

        category_id = self.env.ref('fibernet.installation')

        is_default_installation_group = False
        is_installation_group = self.env['user.ticket.group'].search(
                [('is_installation_group_default_csc', '=', True)],limit=1)
        if not is_installation_group:
            raise UserError(_('Please contact the Administrator to set the Default Installation Group for CSC'))
        elif is_installation_group:
            is_default_installation_group = is_installation_group.id

        # Create ticket
        product_name = False
        product_order_line = self.order_line.filtered(lambda line: line.product_id.is_sub == True)
        if product_order_line :
            product = product_order_line.product_id.id
            product_name = product_order_line.product_id.name
        else:
            product = False
        vals = {
            'name': '%s Installation Ticket for %s with sales order reference (%s)' %  (product_name or '', self.partner_id.name ,  self.name),
            'category_id': category_id.id,
            'partner_id': self.partner_id.id,
            'ticket_company_id' : self.company_id.id,
            'initiator_ticket_group_id' : is_default_installation_group,
            'description' : 'Kindly proceed with the installation of %s for %s (%s) with sales order reference (%s)' %  (product_name or '', self.partner_id.name , self.partner_id.ref, self.name),

        }
        ticket_obj = self.env['kin.ticket'].create(vals)
        self.partner_id.product_id = product
        ticket_obj.order_id = self.id
        ticket_obj.installation_fee = self.order_line.filtered(lambda line: line.product_id.is_sub == False).mapped('price_subtotal')[0]


        grp_name = 'fibernet.group_receive_approve_sale_order_email'
        subject = 'The Sales Order Document %s has been Approved' % self.name
        msg = _('The Sales Order Document %s has been approved by %s, and a new installation ticket has been created') % (
            self.name, self.env.user.name)
        self.send_email(grp_name, subject, msg)


        if self.amount_balance and self.amount_balance > 0:
            debt_msg = '%s has a balance of %s%s, to pay before his account can be activated.  %s should request for the balance payment and contact the accountant to approve the sales order (%s) with the balance before you can re-try finalizing this ticket ' % (
            self.partner_id.name, self.currency_id.symbol, self.amount_balance,
            self.user_id.name, self.name)

            ticket_obj.alert_msg = debt_msg
            ticket_obj.show_alert_box = True

        return res

    def send_email_to_sales_person(self):
        # Send email to sales person
        partn_ids = []
        user = self.user_id
        user_name = user.name
        partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_follower_ids.unlink()
            msg = _(
                'The Sales Order Document %s has been approved by %s.  ') % (
                      self.name, self.env.user.name)
            self.message_post(
                body=msg,
                subject=msg, partner_ids=partn_ids,
                subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_name))

    def action_approve(self):
        return self.action_create_payment_entry()


    def action_disapprove(self, msg):
        self.state = 'draft'
        reason_for_dispproval = msg
        self.disapproved_by_user_id = self.env.user

        # Send email to sales person
        partn_ids = []
        user = self.user_id
        user_name = user.name
        partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_follower_ids.unlink()
            subject = 'The Sales Order Document %s has been Disapproved' % self.name
            msg = _(
                'The Sales Order Document %s has been disapproved by %s. <p><b>Reason for Sales Order Disapproval</b></p><p> %s</p> ') % (
                      self.name, self.env.user.name, reason_for_dispproval)

            self.message_post(
                body=msg,
                subject=subject, partner_ids=partn_ids,
                subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_name))


    
    def action_cancel(self):
        res = super(SaleOrderExtend,self).action_cancel()

        for ticket in self.ticket_ids:
            ticket.unlink()
        self.is_installation_ticket_close = False
        self.is_deferred_payment = False

        if self.payment_ids :
            self.payment_ids.unlink()


        #Send Email
        # company_email = self.env.user.company_id.email
        # sales_person_email = self.user_id.partner_id.email
        # confirm_person_email = self.env.user.partner_id.email
        #
        # if company_email and sales_person_email and confirm_person_email and  (sales_person_email != confirm_person_email ):
        #     # Custom Email Template
        #     mail_template = self.env.ref('kkon_modifications.mail_templ_sale_canceled')
        #     ctx = {}
        #     ctx.update({'sale_id':self.id})
        #     the_url = self._get_sale_order_url('sale','menu_sale_order','action_orders',ctx)
        #
        #     ctx = {'system_email': company_email,
        #             'confirm_person_name': self.env.user.name ,
        #             'confirm_person_email' :confirm_person_email,
        #             'url':the_url
        #             }
        #     mail_template.with_context(ctx).send_mail(self.id,force_send=False)
        return res

    
    def write(self, vals):
        new_state = vals.get('state',False)
        res = super(SaleOrderExtend, self).write(vals)
        for rec in self:
            if len(rec.order_line) == 0 :
                raise UserError(_('At Least an Order Line is Required'))
        return res

    def create_sales_order_eservice(self,vals):
        res = self.create(vals)
        res.action_confirm()
        res.action_create_payment(datetime.now(), self.env['account.journal'].browse(12), res.amount_total, 'eservice', res.partner_id)
        res.create_ticket_with_email()
        res.state = 'sale'

        msg = 'message: %s and payload: %s' % (
            res.id, vals)
        self.env['audit.log'].create(
            {
                'name': msg,
                'log_type': 'sale',
                'status': 'success',
                'endpoint': 'create_sales_order_eservice',
                'date': datetime.now(),
                'user_id': self.env.user.id,
            }
        )
        return [res.id,res.name]


    def action_view_ticket(self):
        ticket_ids = self.mapped('ticket_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("kin_helpdesk.action_view_all_tickets")

        if len(ticket_ids) > 1:
            action['domain'] = [('id', 'in', ticket_ids.ids)]
        elif len(ticket_ids) == 1:
            form_view = [(self.env.ref('kin_helpdesk.ticket_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = ticket_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        #action['target'] = 'new'

        context = {
            #'default_move_type': 'out_invoice',
        }
        # if len(self) == 1:
        #     context.update({
        #         'default_partner_id': self.partner_id.id,
        #         'default_partner_shipping_id': self.partner_shipping_id.id,
        #         'default_invoice_payment_term_id': self.payment_term_id.id or self.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
        #         'default_invoice_origin': self.mapped('name'),
        #         'default_user_id': self.user_id.id,
        #     })
        action['context'] = context
        return action





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



    def btn_view_payment(self):
        payment_ids = self.mapped('payment_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_payments")

        if len(payment_ids) > 1:
            action['domain'] = [('id', 'in', payment_ids.ids)]
        elif len(payment_ids) == 1:
            form_view = [(self.env.ref('account.view_account_payment_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = payment_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        #action['target'] = 'new'

        context = {
            #'default_move_type': 'out_invoice',
        }
        # if len(self) == 1:
        #     context.update({
        #         'default_partner_id': self.partner_id.id,
        #         'default_partner_shipping_id': self.partner_shipping_id.id,
        #         'default_invoice_payment_term_id': self.payment_term_id.id or self.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
        #         'default_invoice_origin': self.mapped('name'),
        #         'default_user_id': self.user_id.id,
        #     })
        action['context'] = context
        return action


    def check_debt_customer(self):
        if self.amount_balance and self.amount_balance > 0:
            debt_msg = '%s has a balance of %s%s, to pay before his account can be activated.  %s should request for the balance payment and contact the accountant to approve the sales order (%s) with the balance before you NOC can finalize this ticket ' % (
            self.partner_id.name, self.currency_id.symbol, self.amount_balance,
            self.user_id.name, self.name)

            for ticket in self.ticket_ids:
                ticket.alert_msg = debt_msg
                ticket.show_alert_box = True
        else:
            for ticket in self.ticket_ids:
                ticket.alert_msg = ''
                ticket.show_alert_box = False
        return

    @api.depends('payment_ids')
    def _compute_payment_count(self):
        for rec in self:
            rec.payment_count = len(rec.payment_ids)


    @api.depends('payment_ids.amount')
    def _compute_payment_amount(self):
        for rec in self:
            amount = 0
            if rec.payment_ids:
                for payment_id in rec.payment_ids:
                    amount += payment_id.amount
                rec.total_amount_paid = amount
                rec.amount_balance = rec.amount_total - amount
            else:
                rec.total_amount_paid = 0
                rec.amount_balance = 0
                rec.alert_msg = ''
                rec.show_alert_box = False

    def get_default_payment_term(self):
        res = self.env['account.payment.term'].search([('is_default_payment_term', '=', True)],limit=1)
        return res


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
    is_deferred_payment = fields.Boolean(string='Deferred Payment')
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
    payment_id = fields.Many2one('account.payment',string='Payment')
    payment_ids = fields.One2many('account.payment','sale_id',string='Payments')
    total_amount_paid = fields.Monetary(string='Total Amount Paid', compute='_compute_payment_amount', store=True)
    amount_balance = fields.Monetary(string='Balance to be Paid', compute='_compute_payment_amount', store=True)
    show_alert_box = fields.Boolean(string="Show Alert Box")
    alert_msg = fields.Char(string='Alert Message')
    payment_count = fields.Integer(compute="_compute_payment_count", string='# of Payment', copy=False, default=0)
    is_editable_on_sales = fields.Boolean(related='sale_order_template_id.is_editable_on_sales',string='Is Editable on Sales')
    cust_acct_name = fields.Char(string="Customer's Acct.")
    client_type = fields.Selection([
        ('home', 'Home Use'),
        ('corporate', 'Corporate Use')],string='Client Type')
    is_autosend_invoice = fields.Boolean(string="Auto Send Recurring Invoice", default=True)
    payment_term_id = fields.Many2one('account.payment.term',default=get_default_payment_term)



class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"

    is_editable_on_sales = fields.Boolean(string='Is Editable on Sales Order')
    client_type = fields.Selection([
        ('home', 'Home Use'),
        ('corporate', 'Corporate Use')], string='Client Type')

class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    amount = fields.Float(string='Amount')


class ResPartnerExtend(models.Model):
    _inherit = 'res.partner'

    def auth_eservice(self):
        payload = {
            "user": "erppusher1",
            "pass": "CrU5h3!267^43*#"
        }
        response = requests.post("https://selfcare-backyard-demo.fibernet.ng/apyv1/api-router/auth", data=payload)
        bearer_token = json.loads(response.text).get('token')
        return bearer_token

    def send_email(self, grp_name, subject, msg):
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref(grp_name)

        for user in group_obj.users:
            if user.is_group_email:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

        if partn_ids:
            # self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partn_ids, subtype_xmlid='mail.mt_comment',
                              force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

    def _get_self_care_payload(self):
        if not self.ref:
            raise UserError('Kindly set the client ID')
        if not self.state_ng:
            raise UserError('Kindly set the Client State')
        if not self.city_cust:
            raise UserError('Kindly set the client city')
        if not self.street:
            raise UserError('Kindly set the client address')
        if not self.name:
            raise UserError('Kindly set the client Name')
        if not self.phone:
            raise UserError('Kindly set the client phone number')
        if not self.email:
            raise UserError('Kindly set the client email address')
        if not self.expiration_date:
            raise UserError('Kindly set the client service expiration date')
        if not self.product_id:
            raise UserError('Kindly set the client service package')
        if not self.ip_address:
            raise UserError('Kindly set the client IP address')
        if not self.amount:
            raise UserError('Kindly set the client service package amount')

        payload = {
            "erp_id" : self.id,
            "clientID": self.ref or 'nil',
            "firstname": self.name or 'nil',
            "lastname": "",
            "product_id": self.product_id.id or 'nil',
            "area_id": self.area_id.id or 'nil',
            "company": "",
            "address": self.street or 'nil',
            "city": self.city_cust or 'nil' ,
            "state": self.state_ng or 'nil',
            "phone": self.phone or 'nil',
            "email": self.email or 'nil',
            "expiry_date": str(self.expiration_date) or 'nil',
            "activation_date":  str(self.activation_date) or 'nil',
            "ipaddress": self.ip_address or 'nil',
            "idu_serial_no": self.serial_no or 'nil',
            "olt_id": self.olt_id.id or 'nil',
            "gpon": self.gpon or 'nil',
            "vlan": self.vlan or 'nil'
        }
        return payload


    def action_create_customer_selfcare(self):
        if not self.customer_rank:
            raise UserError('This is to be applied to customers only')
        payload = self._get_self_care_payload()
        try:
            response = requests.post("https://selfcare-backyard-demo.fibernet.ng/apyv1/erp/create-user", data=payload, headers={'Authorization': 'Bearer %s' % (self.auth_eservice())})
            if response.status_code != requests.codes.ok:
                msg = 'error while trying to communicate with eservice with the following message: %s and payload: %s' % (
                    response.text, payload)
                self.env.cr.execute(
                    "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                        urllib.parse.quote(msg), 'sale', 'failed', 'action_create_customer_selfcare', datetime.now(), self.env.user.id))
                raise UserError(response.text)
            else:
                msg = 'message: %s and payload: %s' % (
                    response.text, payload)
                self.env.cr.execute(
                    "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                        urllib.parse.quote(msg), 'sale', 'success', 'action_create_customer_selfcare', datetime.now(), self.env.user.id))
                self.env.cr.execute("update res_partner set selfcare_push = True, selfcare_response = '%s' where id = %s" % (response.text, self.id))
                # send email
                grp_name = 'fibernet.group_receive_push_selfcare_customer_email'
                subject = 'New Customer (%s) with client id: %s, has been pushed by %s' % (self.name,self.ref,self.env.user.name)
                msg = _('%s has Pushed a new Customer (%s), with client id: %s to the selfcare Service') % (
                                self.env.user.name, self.name, self.ref)
                self.send_email(grp_name, subject, msg)
        except Exception as e:
            _logger = logging.getLogger(__name__)
            _logger.exception(e)
            msg = 'action_create_customer_selfcare error while trying to communicate with eservice with the following message: %s' % (
                e)
            self.env.cr.execute(
                "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                    urllib.parse.quote(msg), 'sale', 'failed', 'action_push_customer_eservice', datetime.now(), self.env.user.id))
            raise UserError('ERP while communicating with selfcare (Create Customer Endpoint) has encountered the following error: %s' % (e))



    def action_update_customer_eservice(self):
        if not self.customer_rank:
            raise UserError('This is to be applied to customers only')
        payload = self._get_self_care_payload()

        try:
            response = requests.post("https://selfcare-backyard-demo.fibernet.ng/apyv1/erp/create-user", data=payload, headers={'Authorization': 'Bearer %s' % (self.auth_eservice())})
            if response.status_code != requests.codes.ok:
                msg = 'error while trying to communicate with eservice with the following message: %s and payload: %s' % (
                    response.text, payload)
                self.env.cr.execute(
                    "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                        urllib.parse.quote(msg), 'sale', 'failed', 'action_update_customer_eservice', datetime.now(), self.env.user.id))

                raise UserError(response.text)
            else:
                msg = 'message: %s and payload: %s' % (
                    response.text, payload)
                self.env.cr.execute(
                    "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                        urllib.parse.quote(msg), 'sale', 'success', 'action_update_customer_eservice', datetime.now(), self.env.user.id))

                self.env.cr.execute("update res_partner set selfcare_push = True, selfcare_response = '%s' where id = %s" % (response.text, self.id))
                # send email
                grp_name = 'fibernet.group_receive_push_selfcare_customer_email'
                subject = 'Existing Customer (%s) with client id: %s, has been Updated in ERP and Selfcare Service by %s' % (self.name, self.ref,self.env.user.name)
                msg = _('%s has edited the Customer (%s),  with client id: %s, in ERP and Selfcare Service') % (
                                self.env.user.name, self.name, self.ref)
                self.send_email(grp_name, subject, msg)
        except Exception as e:
            _logger = logging.getLogger(__name__)
            _logger.exception(e)
            msg = 'action_update_customer_eservice error while trying to communicate with eservice with the following message: %s' % (
                e)
            self.env.cr.execute(
                "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                    msg, 'sale', 'failed', 'action_update_customer_eservice', datetime.now(), self.env.user.id))
            raise UserError('ERP while communicating with selfcare (Update Customer Endpoint) has encountered the following error: %s' % (e))



    def action_delete_customer_selfcare(self):
        if not self.customer_rank:
            raise UserError('This is to be applied to customers only')
        payload = {
            'username': self.ref,
            'key': 1899,
        }
        try:
            response = requests.post("http://api.fibernet.ng:8010/api/delete-client", data=payload)
            if response.status_code != requests.codes.ok:
                raise UserError(response.text)
            else:
                # send email
                grp_name = 'fibernet.group_receive_push_selfcare_customer_email'
                subject = 'Existing Customer (%s) with client ID: %s has been deleted from ERP and Self Care by %s' % (self.name,self.ref,self.env.user.name)
                msg = _('%s has deleted the Customer (%s) with client ID: %s in ERP and in Selfcare Service') % (
                                self.env.user.name, self.name, self.ref)
                self.send_email(grp_name, subject, msg)
        except Exception as e:
            _logger = logging.getLogger(__name__)
            _logger.exception(e)
            raise UserError('ERP while communicating with selfcare (Delete Customer Endpoint) has encountered the following error: %s' % (e))


    def btn_push_update_selfcare(self):
        if self.selfcare_push :
            self.action_update_customer_eservice()
        else:
            raise UserError('There is no initial customer created from ERP to selfcare from the installation ticket')

    def write(self,vals):
        res = super(ResPartnerExtend, self).write(vals)
        return res

    def unlink(self):
        for rec in self:
            if rec.selfcare_push:
                rec.action_delete_customer_selfcare()
        return super(ResPartnerExtend, self).unlink()

    def create_customer_eservice(self,vals):
        customer = self.create(vals)

        msg = 'message: %s and payload: %s' % (
            customer.id, vals)
        self.env['audit.log'].create(
            {
                'name': msg,
                'log_type': 'sale',
                'status': 'success',
                'endpoint': 'create_customer_eservice',
                'date': datetime.now(),
                'user_id': self.env.user.id,
            }
        )

        return customer.id

    product_id = fields.Many2one('product.product', string='Package',tracking=True)
    amount = fields.Float(string='Package Amount')
    location_id = fields.Many2one('location',string='Location',tracking=True)
    base_station_id = fields.Many2one('base.station',string='Base Station',tracking=True)
    bandwidth = fields.Char(string='Bandwidth',tracking=True)
    contact_person = fields.Char(string='Contact Person',tracking=True)
    cpe = fields.Char('CPE Model',tracking=True)
    ip_address = fields.Char(string='Customer IP Address',tracking=True)
    radio_ip_address = fields.Char(string='Radio IP Address',tracking=True)
    base_station_ip_address = fields.Char(string='Base Station IP Address',tracking=True)
    subnet = fields.Char(string='Subnet',tracking=True)
    gateway = fields.Char(string='Gateway',tracking=True)
    indoor_wan = fields.Char(string='Indoor WAN IP Address',tracking=True)
    vlan = fields.Char(string='Vlan',tracking=True)
    olt_id = fields.Many2one('olt', string='OLT',tracking=True)
    region_id = fields.Many2one('region', string='Region',tracking=True)
    estate_id = fields.Many2one('estate', string='Estate',tracking=True)
    area_id = fields.Many2one('area',string='Area',tracking=True)
    installation_fse_id = fields.Many2one('res.users', string='Installation FSE', tracking=True)
    power_level_id = fields.Many2one('pl', string='Power Level', tracking=True)
    comment = fields.Char(string='Comment',tracking=True)
    activation_date = fields.Date(string='Activation Date',tracking=True)
    status = fields.Selection([
        ('active', 'Active'),('disabled','Disabled'),
        ('expired', 'Expired')
    ], string='Status',tracking=True)
    gender = fields.Selection([('male','Male'),('female','Female'),('not_set','Not Set')], string='Gender',tracking=True)
    city_cust = fields.Char(string='City',tracking=True)
    dob = fields.Date(string="DOB",tracking=True)
    expiration_date = fields.Date(string="Expiration Date",tracking=True)
    reg_date = fields.Date(string="REG Date",tracking=True)
    last_logoff = fields.Date(string="Last Logoff",tracking=True)
    gpon = fields.Char(string="GPON Port",tracking=True)
    interface = fields.Char(string="Interface",tracking=True)
    serial_no = fields.Char(string="IDU Serial No",tracking=True)
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
    ], string='State',tracking=True)
    user_id = fields.Many2one('res.users', string='Salesperson',  default=lambda self: self.env.user,
                              help='The internal user in charge of this contact.')
    selfcare_push = fields.Boolean(string='Selfcare Pushed')
    selfcare_response = fields.Char(string='Selfcare Response')


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    is_default_payment_term = fields.Boolean(string="Default Payment Term")

class AccountPayment(models.Model):
    _inherit = 'account.payment'


    def amount_to_text(self, amt):
        amount_text = self.currency_id.amount_to_text(amt)
        return str.upper('**** ' + amount_text + '**** ONLY')

    def action_receipt_plain_sent_no_logging_no_button_document(self):
        #this is just raw email without the default sent by footer, view button and there is no email log on the document

        partner_id = self.partner_id
        if not partner_id.email:
            raise UserError(
                'Kindly set the email for the %s with client id %s, in the customers database, before this ticket can be opened' % (
                    partner_id.name, partner_id.ref or ''))

        report = self.env.ref('kin_account.action_report_receipt')._render_qweb_pdf(self.id)
        name = '%s Payment Recieipt (%s)' % (self.env.company.name, self.name)
        filename = name + '.pdf'
        receipt = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(report[0]),
            'store_fname': filename,
            'res_model': 'account.payment',
            'res_id': self.id,
            # 'mimetype': 'application/x-pdf'
        })
        msg = "<p>Dear %s</p><p>Thank you for your payment. See attached document for your payment receipt %s amounting to %s from %s.</p><p>Do not hesitate to contact us if you have any questions.</p><p>Best regards,</p>" % (
        self.partner_id.name, (self.name or '').replace('/', '-'),
        format_amount(self.env, self.amount, self.currency_id), self.company_id.name)
        mail_values = {
            'subject': name,
            'body_html': msg,
            'author_id': self.env.user.partner_id.id,
            'email_from': 'csc@fibernet.ng',
            'email_to': self.partner_id.email,
            'attachment_ids': [(4, receipt.id)],
            'auto_delete': True
        }
        mail_values['attachment_ids'] += [(4, receipt.id)]
        mail = self.env['mail.mail'].create(mail_values)
        #mail.send()
        mail.mark_outgoing()


    sale_id = fields.Many2one('sale.order', string='Sales Order')


class ProductTemplateExtend(models.Model):
    _inherit = 'product.template'

    is_sub = fields.Boolean(string='Is Subscription Package', track_visibility='always')
    selfcare_package_id = fields.Integer(string='Selfcare Package ID', track_visibility='always')


class Prospect(models.Model):
    _name = "prospect"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Prospect'
    _order = 'open_date desc'

    @api.model
    def run_prospect_contacted_check(self):
        now = datetime.now()
        prospects = self.search([('expiry_date', '<', now), ('state', '!=', 'contacted'), ('is_non_compliance_email_sent', '=', False)])

        for prospect in prospects:
            # open_date = prospect.open_date
            # today = datetime.strptime(datetime.today().strftime('%Y-%m-%d %H:%M:%S'), DEFAULT_SERVER_DATETIME_FORMAT)
            # open_date = datetime.strptime(open_date, '%Y-%m-%d %H:%M:%S')
            # date_diff = today - open_date
            # open_date_format = datetime.strptime(open_date, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')

            # send email back to the ticket opener
            partn_ids = []
            user_names = ''
            init_users = prospect.request_ticket_id.initiator_ticket_group_id.sudo().user_ids
            for user in init_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

            if partn_ids:
                subject = 'Sales person (%s) Non-Complaince within the stipulated time ' % (prospect.user_id.name)
                msg = 'The sales person (%s) has failed to contact the new prospect (%s). A debit is applicable to %s, for not contacting the lead within the stipulated time of 30minutes.' % (prospect.user_id.name, prospect.name, prospect.user_id.name)

                prospect.message_post(
                body = msg,
                subject = subject, partner_ids = partn_ids,
                subtype_xmlid = 'mail.mt_comment')
                prospect.is_non_compliance_email_sent = True
                prospect.is_non_compliance_email_sent_date = datetime.now()
        return True


    def btn_contacted(self):

        if not self.comment :
            raise UserError('Please enter your comment before marking this prospect as contacted ')
        self.state = 'contacted'
        self.contacted_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        #send email to ticket opener, which is probably csc group
        users = self.sudo().request_ticket_id.initiator_ticket_group_id.sudo().user_ids
        partn_ids = []
        user_names = ''
        subject = 'The Prospect (%s) has been contacted by %s' % (self.name,  self.env.user.name)
        msg = 'The Prospect (%s) has been contacted by %s with comment: <p>%s</p>' % (
            self.name,  self.env.user.name, self.comment)
        for user in users:
            if user.is_group_email:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_follower_ids.unlink()
            self.message_post(
                body=_(msg),
                subject='%s' % subject, partner_ids=partn_ids, subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

    def btn_reset(self):
        self.state = 'new'

    def btn_close(self):
        self.state = 'close'
        self.request_ticket_id.sudo().btn_ticket_close()
        # send email
        partn_ids = []
        group_obj = self.env.ref('fibernet.group_prospect_request_ticket_close_notify')
        user_names = ''
        for user in group_obj.sudo().users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)

        if partn_ids:
            user = self.env.user.name
            msg = 'The Prospect and Request Ticket (%s) for %s has been sealed by %s' % (
            self.request_ticket_id.ticket_id, self.name, user)
            subject = 'Closure/Sealed notification for the request ticket (%s) by %s' % (
            self.request_ticket_id.ticket_id, user)
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partn_ids, subtype_xmlid='mail.mt_comment',
                              force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))



    def create(self,vals):
        request_ticket_id = vals.get('request_ticket_id', False)
        if not request_ticket_id :
            raise UserError('Sorry, you cannot create a prospect from here. This can only be created from CSC support team')
        res = super(Prospect, self).create(vals)
        return res

    name = fields.Char(string='Name', tracking=True)
    address = fields.Char(string='Address',tracking=True)
    area_id = fields.Many2one('area',string='Area',tracking=True)
    email = fields.Char(string='Email',tracking=True)
    phone = fields.Char(string='Phone',tracking=True)
    comment = fields.Text(string="Comment",tracking=True)
    user_id = fields.Many2one('res.users', string='Sales Person',tracking=True)
    open_date = fields.Datetime(string='Open Date', tracking=True)
    expiry_date = fields.Datetime(string='Expiry Date', tracking=True)
    contacted_date = fields.Datetime(string='Contacted Date',tracking=True)
    state = fields.Selection(
        [('new', 'New'), ('contacted', 'Contacted'),('close','Closed')],
        default='new', tracking=True)
    is_non_compliance_email_sent = fields.Boolean(string='Is Non-Compliance Email Sent', default=False,tracking=True)
    is_non_compliance_email_sent_date = fields.Datetime(string='Non-Compliance Email Sent Date')
    request_ticket_id = fields.Many2one('kin.ticket', string='Request Ticket',tracking=True)


class ResCompany(models.Model):
    _inherit = 'res.company'

    img_signature = fields.Binary(string='Signature Image')