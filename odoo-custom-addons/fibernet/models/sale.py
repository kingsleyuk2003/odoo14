# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
import base64
from datetime import datetime,date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta



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

    def get_payment_type(self):
        is_paid_deferred = False
        product_subscription_line = self.order_line.filtered(lambda line: line.product_id.is_sub == True)
        if product_subscription_line:
            is_paid_deferred = "paid"
        else:
            is_paid_deferred = "deferred"
        return is_paid_deferred


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
            'context': {'default_is_paid_deferred': self.get_payment_type(),'default_partner_id': self.partner_id.id,'default_total_amount_paid': self.total_amount_paid,'default_amount_balance': self.amount_balance or self.amount_total},
            'res_model': action.res_model,
            'target': 'new'
        }


    
    def create_ticket_with_email(self):
        self.state = 'sale'
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


        grp_name = 'fibernet.group_receive_approve_sale_order_email'
        subject = 'The Sales Order Document %s has been Approved' % self.name
        msg = _('The Sales Order Document %s has been approved by %s, and a new installation ticket has been created') % (
            self.name, self.env.user.name)
        self.send_email(grp_name, subject, msg)

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
                'The ddSales Order Document %s has been approved by %s.  ') % (
                      self.name, self.env.user.name)
            self.message_post(
                body=msg,
                subject=msg, partner_ids=partn_ids,
                subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_name))

    def action_approve(self):
        if self.partner_id.ref :
            raise UserError('Sorry, this is not a new customer. You can create a new customer for a new installation')
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
                subject=msg, partner_ids=partn_ids,
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

    
    def action_view_ticket(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Ticket'),
            'view_mode': 'tree,form',
            'res_model': 'kin.ticket',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.ticket_ids])],
            'target': 'new'
        }


    def action_view_ticket(self):
        ticket_ids = self.mapped('ticket_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('kin_helpdesk.action_view_all_tickets')
        list_view_id = imd.xmlid_to_res_id('kin_helpdesk.ticket_tree_view')
        form_view_id = imd.xmlid_to_res_id('kin_helpdesk.ticket_form')

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
        if len(ticket_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % ticket_ids.ids
        elif len(ticket_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = ticket_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

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
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_account_payments')
        list_view_id = imd.xmlid_to_res_id('account.view_account_payment_tree')
        form_view_id = imd.xmlid_to_res_id('account.view_account_payment_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'target': 'new',
        }
        if len(payment_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % payment_ids.ids
        elif len(payment_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = payment_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


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
   

class ResPartnerExtend(models.Model):
    _inherit = 'res.partner'


    @api.model
    def create(self, vals):
        # is_parent_id = vals.get('parent_id',False)
        # if not is_parent_id :
        #     vals['ref'] = self.env['ir.sequence'].next_by_code('fn_code')
        res = super(ResPartnerExtend,self).create(vals)
        return res

    
    def write(self, vals):
        res = super(ResPartnerExtend, self).write(vals)
        # for rec in self:
        #     is_parent_id = rec.parent_id
        #     client_id = rec.ref
        #     if not is_parent_id and not client_id :
        #         vals['ref'] = self.env['ir.sequence'].next_by_code('fn_code')
        return res

    

    product_id = fields.Many2one('product.product', string='Package',tracking=True)
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
    gpon = fields.Char(string="GPON",tracking=True)
    interface = fields.Char(string="Interface",tracking=True)
    serial_no = fields.Char(string="Serial No",tracking=True)
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


from odoo.tools.misc import format_amount

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
        mail = self.env['mail.mail'].sudo().create(mail_values)
        #mail.send()
        mail.mark_outgoing()


    sale_id = fields.Many2one('sale.order', string='Sales Order')


class ProductTemplateExtend(models.Model):
    _inherit = 'product.template'

    is_sub = fields.Boolean(string='Is Subscription Package', track_visibility='always')


class Prospect(models.Model):
    _name = "prospect"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Prospect'

    @api.model
    def run_prospect_contacted_check(self):
        the_date = datetime.today() + relativedelta(minutes=+30)
        prospects = self.search([('open_date', '<', the_date), ('state', '!=', 'contacted'), ('is_non_compliance_email_sent', '=', False)])

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
                msg = 'The sales person (%s) has failed to contact the new prospect (%s). A debit is applicable for %s, for not contacting the lead within the stipulated time of 30minutes.' % (prospect.user_id.name, prospect.name, prospect.user_id.name)

                prospect.message_post(
                body = msg,
                subject = subject, partner_ids = partn_ids,
                subtype_xmlid = 'mail.mt_comment')
                prospect.is_non_compliance_email_sent = True
        return True



    def btn_contacted(self):

        if not self.comment :
            raise UserError('Please enter your comment before making this prospect as contacted ')
        self.state = 'contacted'
        self.contacted_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        #send email to ticket opener, which is probably csc group
        users = self.request_ticket_id.initiator_ticket_group_id.sudo().user_ids
        partn_ids = []
        user_names = ''
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
                subject='%s' % msg, partner_ids=partn_ids, subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

    def btn_reset(self):
        self.state = 'new'

    name = fields.Char(string='Name', tracking=True)
    address = fields.Char(string='Address',tracking=True)
    area_id = fields.Many2one('area',string='Area',tracking=True)
    email = fields.Char(string='Email',tracking=True)
    phone = fields.Char(string='Phone',tracking=True)
    comment = fields.Text(string="Comment",tracking=True)
    user_id = fields.Many2one('res.users', string='Sales Person',tracking=True)
    open_date = fields.Datetime(string='Open Date', default=datetime.now(),tracking=True)
    contacted_date = fields.Datetime(string='Contacted Date',tracking=True)
    state = fields.Selection(
        [('new', 'New'), ('contacted', 'Contacted')],
        default='new', tracking=True)
    is_non_compliance_email_sent = fields.Boolean(string='Is Non-Compliance Email Sent', default=False,tracking=True)
    request_ticket_id = fields.Many2one('kin.ticket', string='Request Ticket',tracking=True)