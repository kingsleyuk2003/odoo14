# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from datetime import datetime,date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import requests, logging
import pytz

class UserGroups(models.Model):
    _inherit = 'user.ticket.group'
    _description = 'User Ticket Group'

    is_eng_default = fields.Boolean(string='Is Assigned Team Default')
    is_intg_default = fields.Boolean(string='Is Finalized Default')
    is_survey_group_default_csc = fields.Boolean(string='Is Survey Group Default')
    is_installation_group_default_csc = fields.Boolean(string='Is Installation Group Default for CSC')
    is_csc_group = fields.Boolean(string='Is CSC Group')
    is_request_ticket_group = fields.Boolean(string='Is Request Ticket Group')




class Estate(models.Model):
    _name = "estate"
    _description = 'Estate'

    name = fields.Char(string='Estate')

class OLT(models.Model):
    _name = "olt"
    _description = 'OLT'

    name = fields.Char(string='OLT')


class PowerLevel(models.Model):
    _name = "pl"
    _description = 'Power Level'

    name = fields.Char(string='Power Level')

class REGION(models.Model):
    _name = "region"
    _description = 'Region'


    def create(self,vals):
        region = super(REGION, self).create(vals)
        region.action_create_region_eservice()
        return region

    def action_create_region_eservice(self):
        payload =  {
            'name': self.name or 'nil',
        }
        try:
            response = requests.post("http://api.fibernet.ng:8010/api/create-client", data=payload)
            if response.status_code != requests.codes.ok:
                msg = 'error while trying to communicate with eservice with the following message: %s and payload: %s' % (
                    response.text, payload)
                self.env.cr.execute(
                    "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES (%s, %s, %s, %s,'%s','%s')" % (
                        msg, 'ticket', 'failed', 'action_create_region_eservice', datetime.now(), self.env.user))

                raise UserError(response.text)
            else:
                msg = 'message: %s and payload: %s' % (
                    response.text, payload)
                self.env.cr.execute(
                    "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                        msg, 'ticket', 'success', 'action_create_region_eservice', datetime.now(), self.env.user))
        except Exception as e:
            _logger = logging.getLogger(__name__)
            _logger.exception(e)
            msg = 'action_create_customer_selfcare error while trying to communicate with eservice with the following message: %s' % (
                e)
            self.env.cr.execute(
                "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                    msg, 'ticket', 'failed', 'action_create_region_eservice', datetime.now(), self.env.user))
            raise UserError('ERP while communicating with selfcare (Create Region Endpoint) has encountered the following error: %s' % (e))


    name = fields.Char(string='Region')



class Area(models.Model):
    _name = "area"
    _description = 'Area'

    @api.model
    def create(self, vals):
        prefix = vals.get('prefix',False)
        if prefix :
            IrSequence = self.env['ir.sequence'].sudo()
            company_id = self.env.company.id
            val = {
                'name': _('%s Sequence', vals['name']),
                'padding': 4,
                'number_next': 1,
                'number_increment': 1,
                'prefix': "%s" % vals['prefix'],
                'code': '%s-code' % (vals['prefix']),
                'company_id': company_id,
            }
            vals['sequence_id'] = IrSequence.create(val).id

        area = super(Area, self).create(vals)
        area.action_create_area_eservice()
        return area

    def action_create_area_eservice(self):
        payload =  {
            'name': self.name or 'nil',
        }
        try:
            response = requests.post("http://api.fibernet.ng:8010/api/create-client", data=payload)
            if response.status_code != requests.codes.ok:

                msg = 'error while trying to communicate with eservice with the following message: %s and payload: %s' % (
                    response.text, payload)
                self.env.cr.execute(
                    "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                        msg, 'ticket', 'failed', 'action_create_area_eservice', datetime.now(), self.env.user))

                raise UserError(response.text)
            else:
                msg = 'message: %s and payload: %s' % (
                    response.text, payload)
                self.env.cr.execute(
                    "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                        msg, 'ticket', 'success', 'action_create_area_eservice', datetime.now(), self.env.user))
        except Exception as e:
            _logger = logging.getLogger(__name__)
            _logger.exception(e)
            msg = 'action_create_area_eservice error while trying to communicate with eservice with the following message: %s' % (
                e)
            self.env.cr.execute(
                "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                    msg, 'ticket', 'failed', 'action_create_area_eservice', datetime.now(), self.env.user))
            raise UserError('ERP while communicating with selfcare (Create Area Endpoint) has encountered the following error: %s' % (e))



    name = fields.Char(string='Area')
    area_manager_id = fields.Many2one('res.users',string="Area Manager")
    sales_person_id = fields.Many2one('res.users', string="Sales Person")
    user_ticket_group_id = fields.Many2one('user.ticket.group', string='Engineer User Ticket Group')
    prefix = fields.Char(string='Prefix')
    sequence_id = fields.Many2one('ir.sequence', string="Sequence",ondelete="restrict")
    is_others = fields.Boolean(string="Is Others", default=False)
    ticket_count_per_day = fields.Integer(string="Ticket Count Per Day", default=4, tracking=True)
    installation_day_offset = fields.Integer(string="Installation Day Offset", help="How many days added to Opened ticket to get the installation date", default=2,tracking=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Area name must be unique !'),
        ('prefix_uniq', 'unique(prefix)', 'Prefix must be unique !'),
    ]



class CompliantType(models.Model):
    _name = "complaint.type"
    _description = 'Complaint Type'

    name = fields.Char(string='Compliant Type')

class RSSI(models.Model):
    _name = "rssi"
    _description = 'RSSI'

    name = fields.Char(string='RSSI')

class ElapsedHoursFirst(models.Model):
    _name = "elapsed.hour.first"
    _description = 'Elapsed Hour First'

    day_no = fields.Integer(string="Day No.")
    elapsed_hours = fields.Integer(string="Elapsed Hours")
    ticket_id = fields.Many2one('kin.ticket',  string='Ticket')



class ElapsedHoursSecond(models.Model):
    _name = "elapsed.hour.second"
    _description = 'Elapsed Hour Second'

    day_no = fields.Integer(string="Day No.")
    elapsed_hours = fields.Integer(string="Elapsed Hours")
    ticket_id = fields.Many2one('kin.ticket',  string='Ticket')


class ElapsedHoursThird(models.Model):
    _name = "elapsed.hour.third"
    _description = 'Elapsed Hour Third'

    day_no = fields.Integer(string="Day No.")
    elapsed_hours = fields.Integer(string="Elapsed Hours")
    ticket_id = fields.Many2one('kin.ticket',  string='Ticket')


class TicketCategory(models.Model):
    _inherit = 'kin.ticket.category'

    user_ticket_group_id = fields.Many2one('user.ticket.group', string='Default User Ticket Group')

class Ticket(models.Model):
    _inherit = 'kin.ticket'
    _rec_name = 'ticket_id'

    @api.model
    def run_escalate_check(self):

        now = datetime.now()
        records = self.search([('expiry_date', '<', now), ('state', 'not in', ('draft','closed')), ('is_escalation_email_sent', '=', False)])

        for record in records:
            # open_date = prospect.open_date
            # today = datetime.strptime(datetime.today().strftime('%Y-%m-%d %H:%M:%S'), DEFAULT_SERVER_DATETIME_FORMAT)
            # open_date = datetime.strptime(open_date, '%Y-%m-%d %H:%M:%S')
            # date_diff = today - open_date
            # open_date_format = datetime.strptime(open_date, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')

             # send email
            partn_ids = []
            user_names = ''
            group_obj = self.env.ref('fibernet.group_receive_ticket_escalation_email')
            for user in group_obj.users:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

            if partn_ids:
                subject = '%s Ticket (%s) Escalation Notification' % (record.category_id.name,record.ticket_id)
                msg = 'The is to inform you that the ticket (%s) with id: (%s) , for the category (%s) has not be closed within the stipulated time of 30minutes.' % (record.name,record.ticket_id, record.category_id.name)

                record.message_post(
                body = msg,
                subject = subject, partner_ids = partn_ids,
                subtype_xmlid = 'mail.mt_comment')
                record.is_escalation_email_sent = True
                record.is_escalation_email_sent_date = datetime.now()
        return True

    @api.model
    def run_installation_date_check(self):
        tommorrow = datetime.now() + relativedelta(days=+int(1))
        records = self.search([('category_id','=',self.env.ref('fibernet.installation').id),('installation_date', '=', tommorrow), ('state', 'not in', ['draft', 'closed','cancel'])])

        for record in records:
            # Send email to customer and sales person
            installation_date = record.installation_date.strftime('%d/%m/%Y')
            partner_id = record.partner_id
            user_names = ''
            if partner_id and record.category_id == record.env.ref('fibernet.installation'):
                if not partner_id.email:
                    raise UserError(
                        'Kindly set the email for the %s with client id %s, in the customers database' % (
                            partner_id.name, partner_id.ref or ''))

                msg = 'Dear %s, <p>We shall be in your apartment tomorrow for your internet installation tomorrow, %s within 8am-5pm.</p><p>We shall need access to your apartment and an adult that can give us directions for us to achieve the installation. </p><p>Kindly let us know if you will not be available for the installation to be carried out. </p><p>If you have any questions or require further assistance, please do not hesitate to contact our customer support team at </p><p><ul class=o_timeline_tracking_value_list><li>Calls:  02018889028</li><li>Whatsapp: +234 907 101 1409</li><li>Email: onboarding@fibernet.ng</li></ul></p><p> Thank you for choosing Fibernet Broadband Limited. We are committed to delivering excellence and exceeding your expectations.</p><p>Best Regards,</p><p>Customer Onboarding/Retention Center</p>' % \
                      (
                          partner_id.name, installation_date)
                record.message_follower_ids.unlink()
                mail_obj = record.message_post(
                    body=_(msg),
                    subject='Installation Reminder: Your internet Installation is Scheduled for Tomorrow %s' % (installation_date), partner_ids=[partner_id.id],
                    subtype_xmlid='mail.mt_comment', force_send=False)
                user_names += partner_id.name + ", "
                mail_obj.email_from = 'onboarding@fibernet.ng'
                mail_obj.reply_to = 'onboarding@fibernet.ng'

                # notify sales person
                if record.order_id.user_id:
                    subject = 'For your information. Reminder Installation Notification for %s, is scheduled on %s' % (
                        record.partner_id.name, installation_date)
                    smsg = "<p> Dear %s </p><p> Kindly see the message below for your reference </p> <br />" % record.order_id.user_id.name
                    record._send_email_to_sales_person(subject, smsg + msg)
        return True

    @api.model
    def run_installation_date_today_check(self):
        today = datetime.now()
        records = self.search(
            [('category_id', '=', self.env.ref('fibernet.installation').id), ('installation_date', '=', today),
             ('state', 'not in', ['draft', 'closed', 'cancel'])])

        for record in records:
            # Send email to customer and sales person
            installation_date = record.installation_date.strftime('%d/%m/%Y')
            partner_id = record.partner_id
            user_names = ''
            if partner_id and record.category_id == record.env.ref('fibernet.installation'):
                if not partner_id.email:
                    raise UserError(
                        'Kindly set the email for the %s with client id %s, in the customers database' % (
                            partner_id.name, partner_id.ref or ''))

                msg = 'Dear %s, <p>We shall be in your apartment today for your internet installation, %s within 8am-5pm.</p><p>We shall need access to your apartment and an adult that can give us directions for us to achieve the installation. </p><p>Kindly let us know if you will not be available for the installation to be carried out. </p><p>If you have any questions or require further assistance, please do not hesitate to contact our customer support team at </p><p><ul class=o_timeline_tracking_value_list><li>Calls:  02018889028</li><li>Whatsapp: +234 907 101 1409</li><li>Email: onboarding@fibernet.ng</li></ul></p><p> Thank you for choosing Fibernet Broadband Limited. We are committed to delivering excellence and exceeding your expectations.</p><p>Best Regards,</p><p>Customer Onboarding/Retention Center</p>' % \
                      (
                          partner_id.name, installation_date)
                record.message_follower_ids.unlink()
                mail_obj = record.message_post(
                    body=_(msg),
                    subject='Installation Reminder: Your internet Installation is Today %s' % (
                        installation_date), partner_ids=[partner_id.id],
                    subtype_xmlid='mail.mt_comment', force_send=False)
                user_names += partner_id.name + ", "
                mail_obj.email_from = 'onboarding@fibernet.ng'
                mail_obj.reply_to = 'onboarding@fibernet.ng'

                # notify sales person
                if record.order_id.user_id:
                    subject = 'For your information. Reminder Installation Notification for %s, is scheduled on %s' % (
                        record.partner_id.name, installation_date)
                    smsg = "<p> Dear %s </p><p> Kindly see the message below for your reference </p> <br />" % record.order_id.user_id.name
                    record._send_email_to_sales_person(subject, smsg + msg)

        return True


    @api.model
    def run_escalate_installation_date_check(self):
        now = datetime.now()
        records = self.search([('category_id','=',self.env.ref('fibernet.installation').id),('installation_date', '<', now), ('state', 'not in', ['draft','done','finalized','closed','cancel'])])

        for record in records:
            # send email
            partn_ids = []
            user_names = ''
            group_obj = self.env.ref('fibernet.group_ticket_installation_date_failed_notify')
            for user in group_obj.users:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

            if partn_ids:
                subject = 'Failed Installation Ticket (%s) Escalation in %s  with description (%s)' % (record.ticket_id,record.area_customer_id.name,record.name)
                msg = 'The is to inform you that the ticket (%s) for the customer %s, with ticket id: (%s) for the area %s, has failed the scheduled installation date set at %s' % (
                record.name, record.partner_id.name, record.ticket_id, record.area_customer_id.name,record.installation_date.strftime('%d/%m/%Y'))

                record.message_post(
                    body=msg,
                    subject=subject, partner_ids=partn_ids,
                    subtype_xmlid='mail.mt_comment')
        return True



    @api.model
    def run_support_date_check(self):
        tommorrow = datetime.now() + relativedelta(days=+int(1))
        records = self.search([('category_id','=',self.env.ref('fibernet.support').id),('support_date', '=', tommorrow), ('state', 'not in', ['draft', 'closed','cancel'])])

        for record in records:
            # Send email to customer and sales person
            support_date = record.support_date.strftime('%d/%m/%Y')
            partner_id = record.partner_id
            user_names = ''
            if partner_id and record.category_id == record.env.ref('fibernet.support'):
                if not partner_id.email:
                    raise UserError(
                        'Kindly set the email for the %s with client id %s, in the customers database' % (
                            partner_id.name, partner_id.ref or ''))

                msg = 'Dear %s, <p>We shall be in your apartment tomorrow for your internet support tomorrow, %s within 8am-5pm.</p><p>We shall need access to your apartment and an adult that can give us directions for us to achieve the maintenance. </p><p>Kindly let us know if you will not be available for the support to be carried out. </p><p>If you have any questions or require further assistance, please do not hesitate to contact our customer support team at </p><p><ul class=o_timeline_tracking_value_list><li>Calls:  02018889028</li><li>Whatsapp: +234 907 101 1409</li><li>Email: onboarding@fibernet.ng</li></ul></p><p> Thank you for choosing Fibernet Broadband Limited. We are committed to delivering excellence and exceeding your expectations.</p><p>Best Regards,</p><p>Customer Support Center</p>' % \
                      (
                          partner_id.name, support_date)
                record.message_follower_ids.unlink()
                mail_obj = record.message_post(
                    body=_(msg),
                    subject='Support Reminder: Your internet Support is Scheduled for Tomorrow %s' % (support_date), partner_ids=[partner_id.id],
                    subtype_xmlid='mail.mt_comment', force_send=False)
                user_names += partner_id.name + ", "
                mail_obj.email_from = 'support@fibernet.ng'
                mail_obj.reply_to = 'support@fibernet.ng'

                # notify ticket opener
                if record.order_id.user_id:
                    subject = 'For your information. Reminder support Notification for %s, is scheduled on %s' % (
                        record.partner_id.name, support_date)
                    smsg = "<p> Dear %s </p><p> Kindly see the message below for your reference </p> <br />" % record.order_id.user_id.name
                    record._send_email_to_ticket_opener(subject, smsg + msg)
        return True

    @api.model
    def run_support_date_today_check(self):
        today = datetime.now()
        records = self.search(
            [('category_id', '=', self.env.ref('fibernet.support').id), ('support_date', '=', today),
             ('state', 'not in', ['draft', 'closed', 'cancel'])])

        for record in records:
            # Send email to customer and sales person
            support_date = record.support_date.strftime('%d/%m/%Y')
            partner_id = record.partner_id
            user_names = ''
            if partner_id and record.category_id == record.env.ref('fibernet.support'):
                if not partner_id.email:
                    raise UserError(
                        'Kindly set the email for the %s with client id %s, in the customers database' % (
                            partner_id.name, partner_id.ref or ''))

                msg = 'Dear %s, <p>We shall be in your apartment today for your internet support, %s within 8am-5pm.</p><p>We shall need access to your apartment and an adult that can give us directions for us to achieve the support. </p><p>Kindly let us know if you will not be available for the support to be carried out. </p><p>If you have any questions or require further assistance, please do not hesitate to contact our customer support team at </p><p><ul class=o_timeline_tracking_value_list><li>Calls:  02018889028</li><li>Whatsapp: +234 907 101 1409</li><li>Email: support@fibernet.ng</li></ul></p><p> Thank you for choosing Fibernet Broadband Limited. We are committed to delivering excellence and exceeding your expectations.</p><p>Best Regards,</p><p>Customer Support Center</p>' % \
                      (
                          partner_id.name, support_date)
                record.message_follower_ids.unlink()
                mail_obj = record.message_post(
                    body=_(msg),
                    subject='support Reminder: Your internet support is Today %s' % (
                        support_date), partner_ids=[partner_id.id],
                    subtype_xmlid='mail.mt_comment', force_send=False)
                user_names += partner_id.name + ", "
                mail_obj.email_from = 'support@fibernet.ng'
                mail_obj.reply_to = 'support@fibernet.ng'

                # notify ticket opener
                if record.order_id.user_id:
                    subject = 'For your information. Reminder support Notification for %s, is scheduled on %s' % (
                        record.partner_id.name, support_date)
                    smsg = "<p> Dear %s </p><p> Kindly see the message below for your reference </p> <br />" % record.order_id.user_id.name
                    record._send_email_to_ticket_opener(subject, smsg + msg)

        return True


    @api.model
    def run_escalate_support_date_check(self):
        now = datetime.now()
        records = self.search([('category_id','=',self.env.ref('fibernet.support').id),('support_date', '<', now), ('state', 'not in', ['draft','done','finalized','closed','cancel'])])

        for record in records:
            # send email
            partn_ids = []
            user_names = ''
            group_obj = self.env.ref('fibernet.group_ticket_support_date_failed_notify')
            for user in group_obj.users:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

            if partn_ids:
                subject = 'Failed support Ticket (%s) Escalation in %s  with description (%s)' % (record.ticket_id,record.area_customer_id.name,record.name)
                msg = 'The is to inform you that the ticket (%s) for the customer %s, with ticket id: (%s) for the area %s, has failed the scheduled support date set at %s' % (
                record.name, record.partner_id.name, record.ticket_id, record.area_customer_id.name,record.support_date.strftime('%d/%m/%Y'))

                record.message_post(
                    body=msg,
                    subject=subject, partner_ids=partn_ids,
                    subtype_xmlid='mail.mt_comment')
        return True

    @api.onchange('category_id')
    def _set_assigned_user_group_from_category(self):
        for rec in self:
            if self.category_id.code in ('backend_support', 'request'):
                self.user_ticket_group_id = self.category_id.user_ticket_group_id

    @api.onchange('area_customer_id')
    def _set_assigned_user_group_from_area(self):
        for rec in self:
            user_ticket_group_id = rec.area_customer_id.user_ticket_group_id
            request_ticket_group = self.env['user.ticket.group'].search([('is_request_ticket_group', '=', True)], limit=1)
            category_code = self.category_id.code
            if user_ticket_group_id:
                rec.user_ticket_group_id = user_ticket_group_id
            if user_ticket_group_id and category_code == 'request':
                rec.user_ticket_group_id = request_ticket_group
                rec.prospect_area_id = self.area_customer_id
            if self.category_id.code in ('backend_support', 'request'):
                self.user_ticket_group_id = self.category_id.user_ticket_group_id


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



    def run_check_expected_finished_date_ticket(self):

        is_send_email_expiry_finish = self.env['ir.config_parameter'].sudo().get_param('fibernet.is_send_email_expiry_finish',default=False)

        if is_send_email_expiry_finish:
            the_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            tickets = self.search([('expected_finish_date', '<', the_date), ('state', '!=', 'closed')])

            for ticket in tickets:
                exp_date = ticket.expected_finish_date
                today = datetime.strptime(datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                                          DEFAULT_SERVER_DATETIME_FORMAT)
                expiry_date = datetime.strptime(exp_date, '%Y-%m-%d %H:%M:%S')
                date_diff = today - expiry_date

                exp_date_format = datetime.strptime(exp_date, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')

                partn_ids = []
                user_names = ''

                init_users = ticket.initiator_ticket_group_id.sudo().user_ids
                for user in init_users:
                    if user.is_group_email:
                        user_names += user.name + ", "
                        partn_ids.append(user.partner_id.id)

                assign_users = ticket.user_ticket_group_id.sudo().user_ids
                for user in assign_users:
                    if user.is_group_email:
                        user_names += user.name + ", "
                        partn_ids.append(user.partner_id.id)

                if partn_ids:
                    self.message_follower_ids.unlink()
                    msg = _('The support Ticket (%s) with subject (%s), having expected finished date as %s, is overdue for closure, by %s hours') % (ticket.ticket_id,ticket.name, exp_date_format,date_diff)
                    self.message_post(
                        body=msg,
                        subject=msg, partner_ids=partn_ids,
                        subtype_xmlid='mail.mt_comment', force_send=False)

            return True


    def btn_ticket_progress(self):
        if self.category_id.code in ('backend_support', 'request'):
            self.user_ticket_group_id = self.category_id.user_ticket_group_id
        return super(Ticket,self).btn_ticket_progress()


    def create_prospect_with_email(self):
        sales_person =  self.others_sales_person_id or self.prospect_area_id.sales_person_id
        if not sales_person :
            raise UserError('Contact your Admin to set the sales person for the area')
        vals =  {
                'name':self.prospect_name,
                'address': self.prospect_address,
                'area_id' :self.prospect_area_id.id,
                'email' : self.prospect_email,
                'phone': self.prospect_phone,
                'user_id': sales_person.id ,
                'request_ticket_id' : self.id,
                'open_date' : datetime.now(),
                'expiry_date': datetime.now() + relativedelta(minutes=+30),
            }
        prospect = self.env['prospect'].create(vals)
        self.prospect_id = prospect

        # Send email to sales person
        partn_ids = []
        user = sales_person
        user_name = user.name
        partn_ids.append(user.partner_id.id)

        if partn_ids:
            prospect.message_follower_ids.unlink()
            msg = _(
                'A prospect (%s)  has been created from the request ticket with id: %s by %s. You are required to contact this prospect, within 30mins  and mark the prospect as contacted on your erp system.   ') % (
                      self.prospect_name, self.name, self.env.user.name)
            self.message_post(
                body=msg,
                subject=msg, partner_ids=partn_ids,
                subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_name))




    # reference: https://stackoverflow.com/a/12691993
    # adds days except weekends
    def get_installation_date(self, from_date, add_days):
        business_days_to_add = add_days
        install_date = from_date
        while business_days_to_add > 0:
            install_date += timedelta(days=1)
            weekday = install_date.weekday()
            if weekday > 4:  # saturday = 5 and sunday = 6
                continue
            business_days_to_add -= 1
        return install_date

    def schedule_installation_date(self,next_day):
        installation_day_offset = self.area_customer_id.installation_day_offset
        ticket_count_per_day = self.area_customer_id.ticket_count_per_day
        from_date = datetime.now() + relativedelta(days=+int(next_day))
        installation_date = self.get_installation_date(from_date, installation_day_offset)
        records = self.search([('state', 'not in', ['draft']),('area_customer_id', '=', self.area_customer_id.id), ('installation_date', '=', installation_date)])

        if len(records) < ticket_count_per_day and self.category_id == self.env.ref('fibernet.installation'):
            self.installation_date = installation_date
            return True
        return False

    def get_installation_date_eservice(self,next_day,installation_day_offset):
        from_date = datetime.now() + relativedelta(days=+int(next_day))
        installation_date = self.get_installation_date(from_date, installation_day_offset)
        return installation_date

    def schedule_installation_date_eservice(self,next_day,area,installation_day_offset,ticket_count_per_day):
        from_date = datetime.now() + relativedelta(days=+int(next_day))
        installation_date = self.get_installation_date(from_date, installation_day_offset)
        records = self.search([('state', 'not in', ['draft']),('area_customer_id', '=', area.id), ('installation_date', '=', installation_date)])

        if len(records) < ticket_count_per_day:
             return True
        return False


    def get_proposed_installation_date_eservice(self,area_id):
        next_day = 0
        area = self.env['area'].browse(area_id)
        installation_day_offset = area.installation_day_offset
        ticket_count_per_day = area.ticket_count_per_day
        while not  self.schedule_installation_date_eservice(next_day,area,installation_day_offset,ticket_count_per_day):
            next_day += 1
            continue
        installation_date = self.get_installation_date_eservice(next_day,installation_day_offset).strftime('%d/%m/%Y')

        msg = "message: %s and payload: %s" % (
            installation_date, area_id)
        self.env.cr.execute(
            "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                msg, 'ticket', 'success', 'create_customer_eservice', datetime.now(), self.env.user.id))

        return installation_date

    def create_support_ticket_eservice(self, vals):
        ticket_id = self.create(vals)
        msg = 'message: %s and payload: %s' % (
            ticket_id, vals)
        self.env.cr.execute(
            "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                msg, 'ticket', 'success', 'create_support_ticket_eservice', datetime.now(), self.env.user))
        return ticket_id.id

    def receive_ticket_comment_eservice(self,vals):
        msg_id = self.env['mail.message'].create({
            'subject': 'Eservice Comment',
            'email_from': 'Eservice',
            'message_type': 'comment',
            'model': 'kin.ticket',
            'body': vals,
        })
        msg = 'message: %s and payload: %s' % (
            msg_id, vals)
        self.env.cr.execute(
            "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                msg, 'ticket', 'success', 'receive_ticket_comment_eservice', datetime.now(), self.env.user))

        return msg_id

    def send_ticket_comment_eservicec(self):
        payload = {
            'username': self.ref,
            'key': 1899,
        }
        try:
            response = requests.post("http://api.fibernet.ng:8010/api/delete-client", data=payload)
            if response.status_code != requests.codes.ok:
                msg = 'error while trying to communicate with eservice with the following message: %s and payload: %s' % (
                    response.text, payload)
                self.env.cr.execute(
                    "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                        msg, 'ticket', 'failed', 'send_ticket_comment_eservice', datetime.now(), self.env.user))
                raise UserError(response.text)
            else:
                msg = 'message: %s and payload: %s' % (
                    response.text, payload)
                self.env.cr.execute(
                    "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                        msg, 'ticket', 'success', 'send_ticket_comment_eservice', datetime.now(), self.env.user))
        except Exception as e:
            _logger = logging.getLogger(__name__)
            _logger.exception(e)
            msg = 'action_create_customer_selfcare error while trying to communicate with eservice with the following message: %s' % (
                e)
            self.env.cr.execute(
                "INSERT INTO audit_log (name,log_type, status, endpoint,  date, user_id) VALUES ('%s', '%s', '%s', '%s','%s','%s')" % (
                    msg, 'ticket', 'failed', 'send_ticket_comment_eservice', datetime.now(), self.env.user))
            raise UserError(
                'ERP while communicating with selfcare (send_ticket_comment_eservice Endpoint) has encountered the following error: %s' % (
                    e))

    def installation_date_change(self,new_installation_date):

        if new_installation_date < date.today():
            raise UserError('You cannot backdate installation')

        ticket_count_per_day = self.area_customer_id.ticket_count_per_day
        records = self.search([('state', 'not in', ['draft']), ('area_customer_id', '=', self.area_customer_id.id),
                               ('installation_date', '=', new_installation_date)])

        if len(records) < ticket_count_per_day and self.category_id == self.env.ref('fibernet.installation'):
            installation_date_conv = False
            if self.installation_date:
                installation_date_conv = self.installation_date.strftime('%d/%m/%Y')
            new_installation_date_conv = new_installation_date.strftime('%d/%m/%Y')
            self.installation_date = new_installation_date

            # Send email to customer and sales person
            partner_id = self.partner_id
            user_names = ''
            if partner_id and self.category_id == self.env.ref('fibernet.installation'):
                if not partner_id.email:
                    raise UserError(
                        'Kindly set the email for the %s with client id %s, in the customers database' % (
                            partner_id.name, partner_id.ref or ''))

                msg = 'Dear %s, <p>This is to notify you that the installation earlier schedule for %s has been rescheduled to %s. This is Due to unforeseen issues concerning the installation process, we have rescheduled the installation to ensure a smooth and efficient setup.</p><p>We apologize for any inconvenience caused by this change. Our team remains committed to providing you with exceptional service and ensuring a flawless installation. We are confident that the rescheduled date will allow us to meet your expectations while delivering the quality you deserve.</p><p>If you have any questions or concerns regarding this rescheduling, please feel free to reach out to our dedicated support team at </p><p><ul class=o_timeline_tracking_value_list><li>Calls:  02018889028</li><li>Whatsapp: +234 907 101 1409</li><li>Email: onboarding@fibernet.ng</li></ul></p><p> We will be happy to address any inquiries you may have and provide you with regular updates as we progress towards the new installation date.</p><p>Thank you for your continued trust and support.</p><p> Regards,</p><p>Customer Onboarding/Retention Center</p>' % \
                      (
                          partner_id.name, installation_date_conv, new_installation_date_conv)
                self.message_follower_ids.unlink()
                mail_obj = self.message_post(
                    body=_(msg),
                    subject='Rescheduled installation for %s' % (partner_id.name), partner_ids=[partner_id.id],
                    subtype_xmlid='mail.mt_comment', force_send=False)
                user_names += partner_id.name + ", "
                mail_obj.email_from = 'onboarding@fibernet.ng'
                mail_obj.reply_to = 'onboarding@fibernet.ng'

                # notify sales person
                if self.sudo().order_id.user_id:
                    subject = 'For your information. Installation for %s, which was scheduled on %s , has been delayed till %s' % (
                        self.partner_id.name, installation_date_conv, new_installation_date_conv)
                    smsg = "<p> Dear %s </p><p> Kindly see the message below for your reference </p> <br />" % self.sudo().order_id.user_id.name
                    self._send_email_to_sales_person(subject, smsg + msg)

                #Send email to authorized group users
                self.send_email('fibernet.group_ticket_installation_date_change_notify',
                                subject='The Ticket Installation date has been changed',
                                msg=_(
                                    'The Installation date for the Ticket %s has been changed for the order id - %s, from %s') % (
                                        self.name, self.sudo().order_id.name, self.env.user.name))



        elif not self.category_id == self.env.ref('fibernet.installation'):
            raise UserError('This not apply to non-installation tickets')
        else:
            raise UserError('Maximum Number (%s) of Installation tickets reached for the set date' % (ticket_count_per_day))


    def support_date_change(self,new_support_date):

        if new_support_date < date.today():
            raise UserError('You cannot backdate support')


        if self.category_id == self.env.ref('fibernet.support'):
            support_date_conv = False
            if self.support_date:
                support_date_conv = self.support_date.strftime('%d/%m/%Y')
            new_support_date_conv = new_support_date.strftime('%d/%m/%Y')
            self.support_date = new_support_date

            # Send email to customer and sales person
            partner_id = self.partner_id
            user_names = ''
            if partner_id and self.category_id == self.env.ref('fibernet.support'):
                if not partner_id.email:
                    raise UserError(
                        'Kindly set the email for the %s with client id %s, in the customers database' % (
                            partner_id.name, partner_id.ref or ''))

                msg = ''
                if support_date_conv :
                    msg = 'Dear %s, <p>This is to notify you that the support earlier schedule for %s has been rescheduled to %s. This is Due to unforeseen issues concerning the support process, we have rescheduled the support to ensure a smooth and efficient setup.</p><p>We apologize for any inconvenience caused by this change. Our team remains committed to providing you with exceptional service and ensuring a flawless support. We are confident that the rescheduled date will allow us to meet your expectations while delivering the quality you deserve.</p><p>If you have any questions or concerns regarding this rescheduling, please feel free to reach out to our dedicated support team at </p><p><ul class=o_timeline_tracking_value_list><li>Calls:  02018889028</li><li>Whatsapp: +234 907 101 1409</li><li>Email: support@fibernet.ng, csc@fibernet.ng</li></ul></p><p> We will be happy to address any inquiries you may have and provide you with regular updates as we progress towards the new support date.</p><p>Thank you for your continued trust and support.</p><p> Regards,</p><p>Customer Support Center</p>' % \
                      (
                          partner_id.name, support_date_conv, new_support_date_conv)
                else:
                    msg = 'Dear %s, <p>This is to notify you that support has been scheduled to %s. we have scheduled the support to ensure a smooth and efficient setup.</p><p>We apologize for any inconvenience. Our team remains committed to providing you with exceptional service and ensuring a flawless support. We are confident that the scheduled date will allow us to meet your expectations while delivering the quality you deserve.</p><p>If you have any questions or concerns regarding this schedule, please feel free to reach out to our dedicated support team at </p><p><ul class=o_timeline_tracking_value_list><li>Calls:  02018889028</li><li>Whatsapp: +234 907 101 1409</li><li>Email: support@fibernet.ng, csc@fibernet.ng</li></ul></p><p> We will be happy to address any inquiries you may have and provide you with regular updates as we progress towards the support date.</p><p>Thank you for your continued trust and support.</p><p> Regards,</p><p>Customer Support Center</p>' % \
                          (
                              partner_id.name,  new_support_date_conv)
                self.message_follower_ids.unlink()
                mail_obj = self.message_post(
                    body=_(msg),
                    subject='Scheduled support for %s' % (partner_id.name), partner_ids=[partner_id.id],
                    subtype_xmlid='mail.mt_comment', force_send=False)
                user_names += partner_id.name + ", "
                mail_obj.email_from = 'support@fibernet.ng'
                mail_obj.reply_to = 'support@fibernet.ng'


                #Send email to authorized group users
                self.send_email('fibernet.group_ticket_support_date_change_notify',
                                subject='The Ticket support date has been changed',
                                msg=_(
                                    'The support date for the Ticket %s has been changed for the order id - %s, from %s') % (
                                        self.name, self.sudo().order_id.name, self.env.user.name))

        elif not self.category_id == self.env.ref('fibernet.support'):
            raise UserError('This not apply to non-support tickets')


    def _send_email_to_sales_person(self,subject,msg):
        # Send email to sales person
        partn_ids = []
        user = self.sudo().order_id.user_id
        partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.sudo().order_id.message_follower_ids.unlink()
            self.sudo().order_id.message_post(
                body=msg,
                subject=subject, partner_ids=partn_ids,
                subtype_xmlid='mail.mt_comment', force_send=False)


    def _send_email_to_ticket_opener(self,subject,msg):
        # email ticket opener users
        partn_ids = []
        user_names = ''

        ope_users = self.initiator_ticket_group_id.sudo().user_ids
        for user in ope_users:
            if user.is_group_email:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_follower_ids.unlink()
            self.message_post(
                body=_(msg),
                subject='%s' % subject, partner_ids=partn_ids, subtype_xmlid='mail.mt_comment', force_send=False)


    def btn_ticket_open(self):

        if self.category_id == self.env.ref('fibernet.installation') and not self.order_id:
            raise UserError('Sorry, you cannot create an installation ticket from here. Contact the sales person to initiate the sales order')

        if not self.category_id or not self.user_intg_ticket_group_id :
            raise UserError(_('Contact the Admin to set the default Finalized group'))

        if self.category_id  in  (self.env.ref('fibernet.support'),self.env.ref('fibernet.updown_grade')) and not self.partner_id.ref:
            raise UserError(_('Set the Customer Client ID on the customers database for this ticket to be opened'))


        if self.category_id.code in ('backend_support','request'):
            self.user_ticket_group_id = self.category_id.user_ticket_group_id

        self.state = 'new'
        self.open_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.user_id = self.env.user

        if self.category_id == self.env.ref('fibernet.request') :
            self.state = 'archived'
            # create prospect with email
            self.create_prospect_with_email()
            return
        else:
            # send email to the Assigned users too
            partn_ids = []
            user_names = ''
            mail_obj = False
            eng_users = self.user_ticket_group_id.sudo().user_ids
            msg = 'The Ticket (%s) with description (%s), has been Opened by %s' % (
                self.ticket_id, self.name, self.env.user.name)
            for user in eng_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

            if partn_ids:
                self.message_follower_ids.unlink()
                mail_obj = self.message_post(
                   body=_(msg),
                    subject='%s' % msg, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)

        if self.category_id in [self.env.ref('fibernet.support')] :
            self.expected_finish_date = datetime.now() + relativedelta(hours=+int(24))

        if self.category_id in [self.env.ref('fibernet.support'),self.env.ref('fibernet.updown_grade')]:
            #send carbon copy email to csc group
            csc_users = []
            user_ticket_groups = self.env.user.user_ticket_group_ids
            for user_ticket_group in user_ticket_groups :
                if user_ticket_group.is_csc_group :
                    csc_users = user_ticket_group.sudo().user_ids

            msg = 'The Ticket (%s) with description (%s), has been Opened by %s' % (
                self.ticket_id, self.name, self.env.user.name)
            partn_csc_ids = []
            for user in csc_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_csc_ids.append(user.partner_id.id)


        #send emails to assigned users groups
        assign_users = self.user_ticket_group_id.sudo().user_ids
        for user in assign_users:
            if user.is_group_email:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

        if partn_ids:
            mesg = 'The Ticket (%s) with description (%s), has been Opened by %s' % (
                self.ticket_id, self.name, self.env.user.name)
            self.message_follower_ids.unlink()
            self.message_post(
                body=_(mesg),
                subject='%s' % mesg, partner_ids=partn_ids, subtype_xmlid='mail.mt_comment', force_send=False)
        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))


        partner_id = self.partner_id
        if partner_id and self.category_id == self.env.ref('fibernet.installation'):
            #schedule installation
            next_day = 0
            while not self.schedule_installation_date(next_day):
                next_day += 1
                continue
            installation_date = self.installation_date.strftime('%d/%m/%Y')

            #send email
            if not partner_id.email:
                raise UserError(
                    'Kindly set the email for the %s with client id %s, in the customers database, before this ticket can be opened' % (
                    partner_id.name, partner_id.ref or ''))

            msg = 'Dear %s, <p>This is to acknowledge the receipt of your payment for (Package-%s) Broadband service. </p> An installation ticket with the ID: %s has been opened for your installation. <p> Your Service ID : %s (this will be required for future communication).</p> <p> Kindly note that your installation has been scheduled for %s between the hours of 8am-5pm. </p> <p> Please note that we will notify you 24 hours before the installation date, to inform you, if there will be change in the scheduled date   </p> <p> For further enquiries and assistance, please feel free to contact us through any of the following channels:</p><p><ul class=o_timeline_tracking_value_list><li>Calls:  02018889028</li><li>Whatsapp: +234 907 101 1409</li><li>Email: onboarding@fibernet.ng</li></ul></p><p>Please visit our website <a href=https://fibernet.ng/ >https://fibernet.ng/</a> for other terms and conditions.</p><p>We appreciate your interest in Fibernet Broadband and we hope you will enjoy our partnership as we provide you a reliable and steady internet connectivity.</p><p> Regards,</p>Customer Service Center</p>' % \
                  (
                      partner_id.name, self.sudo().product_id.name, self.ticket_id, partner_id.ref, installation_date)
            self.message_follower_ids.unlink()
            mail_obj = self.message_post(
                body=_(msg),
                subject='Installation Alert for %s' % (partner_id.name), partner_ids=[partner_id.id],subtype_xmlid='mail.mt_comment', force_send=False)
            user_names += partner_id.name + ", "
            mail_obj.email_from = 'onboarding@fibernet.ng'
            mail_obj.reply_to = 'onboarding@fibernet.ng'
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

            #notify sales person
            if self.sudo().order_id.user_id:
                subject = 'For your information. Installation for %s, has been scheduled on %s' %  (self.partner_id.name, installation_date)
                smsg = "<p> Dear %s </p><p> Kindly see the message below for your reference </p> <br />" % self.sudo().order_id.user_id.name
                self._send_email_to_sales_person(subject, smsg + msg)

        elif partner_id and self.category_id in [self.env.ref('fibernet.support'),self.env.ref('fibernet.updown_grade')]:
            msg = 'Dear %s (%s), <p>We acknowledge the receipt of your complaints dated - %s with ticket ID - %s </p><p>Thank you for bringing this issue to our attention and we sincerely apologize for any inconvenience this may have caused you.</p><p>Please be assured that your complaint is being taken seriously and as such, you will be contacted shortly on necessary action for resolution.</p><p>Thank you for your patience.</p><p> Regards,</p>Customer Service Center</p>' % \
                  (
                partner_id.name,partner_id.ref, datetime.strptime(self.open_date.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y'), self.ticket_id)
            self.message_follower_ids.unlink()
            mail_obj = self.message_post(
                body=_(msg),
                subject='%s Opened Support Ticket Notification for %s' % (self.sudo().product_id.name,partner_id.name), partner_ids=[partner_id.id],subtype_xmlid='mail.mt_comment', force_send=False)
            user_names += partner_id.name + ", "
            mail_obj.email_from = 'csc@fibernet.ng'
            mail_obj.reply_to = 'csc@fibernet.ng'
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        if self.category_id in [self.env.ref('fibernet.backend_support')]:
            self.expiry_date = datetime.now() + relativedelta(minutes=+30)
            # send carbon copy email to assigned group
            csc_users = []
            user_ticket_groups = self.env.user.user_ticket_group_ids
            for user_ticket_group in user_ticket_groups:
                if user_ticket_group.is_csc_group:
                    csc_users = user_ticket_group.sudo().user_ids

            msg = 'The Ticket (%s) with description (%s), has been Opened by %s' % (
                self.ticket_id, self.name, self.env.user.name)
            partn_csc_ids = []
            for user in csc_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_csc_ids.append(user.partner_id.id)

        return



    def _compute_close_duration(self):
        for ticket in self :
            if ticket.open_date and ticket.state not in ('closed','cancel','draft') :
                open_date = ticket.open_date
                now_date = datetime.strptime(datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),DEFAULT_SERVER_DATETIME_FORMAT)
                date_diff =  str(now_date - open_date)
                ticket.duration_close =  date_diff


    def action_view_contract(self):
        contract_id = self.mapped('contract_id')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('contract.action_customer_contract')
        list_view_id = imd.xmlid_to_res_id('contract.contract_contract_tree_view')
        form_view_id = imd.xmlid_to_res_id('contract.contract_contract_customer_form_view')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(contract_id) > 1:
            result['domain'] = "[('id','in',%s)]" % contract_id.id
        elif len(contract_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = contract_id.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.depends('order_id')
    def _compute_contract_count(self):
        for rec in self:
            rec.contract_count = len(rec.contract_id)


    def action_view_order(self):
        order_id = self.mapped('order_id')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders')
        list_view_id = imd.xmlid_to_res_id('sale.view_order_tree')
        form_view_id = imd.xmlid_to_res_id('sale.view_order_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(order_id) > 1:
            result['domain'] = "[('id','in',%s)]" % order_id.id
        elif len(order_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = order_id.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.depends('order_id')
    def _compute_order_count(self):
        for rec in self:
            rec.order_count = len(rec.order_id)

    
    def action_view_invoice(self):
        invoice_id = self.mapped('invoice_id')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_move_out_invoice_type')
        list_view_id = imd.xmlid_to_res_id('account.view_out_invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.view_move_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(invoice_id) > 1:
            result['domain'] = "[('id','in',%s)]" % invoice_id.id
        elif len(invoice_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = invoice_id.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.depends('invoice_id')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_id)


    def create_customer_invoice(self,sale_order):

        if not self.activation_date :
            raise UserError(_('Please Set the Activation Date in the Activation Form Tab'))

        inv = sale_order._create_invoices(final=True)
        inv.sale_ids = sale_order
        inv.action_post()
        inv.is_installation_invoice = True
        inv.installation_ticket_id = self.id
        inv.no_overdue_reminder = True
        self.invoice_id = inv

        #Send Email to accountants.
        # This is sending to other groups that dont need to see it also
        # grp_name = 'account.group_account_invoice'
        # subject = 'A New Sales Quote has been Submitted'
        # msg = _('This installation ticket has been closed by  %s and an invoice has been created for the Ticket with ID %s.') % (
        #                           self.env.user.name, self.name)
        # self.send_email(grp_name, subject, msg)

        return inv


    @api.onchange('partner_id')
    def onchange_partner(self):
        self.product_curr_id = self.partner_id.product_id
        self.bandwidth_current = self.partner_id.bandwidth
        self.address_old = self.partner_id.street
        self.address_ip_current = self.partner_id.ip_address


    @api.onchange('location_id')
    def onchange_location(self):
        self.base_station_id = ''

    @api.onchange('updown_grade_type','area_change_request_id')
    def onchange_updown_grade_type(self):
        if self.updown_grade_type != 'relocation' :
            self.user_ticket_group_id = self.category_id.user_ticket_group_id
        elif self.updown_grade_type == 'relocation' and self.area_change_request_id:
            self.area_customer_id = self.area_change_request_id
            self._set_assigned_user_group_from_area()
        else:
            self._set_assigned_user_group_from_area()


    
    def btn_ticket_reset(self):
        for rec in self:
            rec.invoice_id.unlink()
            rec.is_escalation_email_sent = False
            rec.is_escalation_email_sent_date = False
            rec.expiry_date = False

        if self.category_id == self.env.ref('fibernet.request'):
            self.prospect_id.unlink()
        return super(Ticket, self).btn_ticket_reset()

    
    def btn_ticket_cancel(self):
        for rec in self:
            rec.invoice_id.unlink()
        if self.category_id == self.env.ref('fibernet.request'):
            self.prospect_id.unlink()
        return super(Ticket, self).btn_ticket_cancel()

    
    def unlink(self):
        for rec in self:
            rec.invoice_id.unlink()
        return super(Ticket,self).unlink()

    
    def btn_ticket_done(self):

        if self.category_id.code in ('backend_support', 'request'):
            self.user_ticket_group_id = self.category_id.user_ticket_group_id

        if (self.category_id in (self.env.ref('fibernet.support'), self.env.ref('fibernet.survey'),self.env.ref('fibernet.backend_support'))) or (self.category_id == self.env.ref('fibernet.updown_grade') and self.updown_grade_type != 'relocation') :
            self.state = "finalized"
            self.finalized_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            # email ticket opener users
            partn_ids = []
            user_names = ''
            msg = 'The Ticket (%s) with description (%s), has been completed and finalized by %s, you may now close the ticket' % (
                self.ticket_id, self.name, self.env.user.name)

            ope_users = self.initiator_ticket_group_id.sudo().user_ids
            for user in ope_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

            if partn_ids:
                self.message_follower_ids.unlink()
                self.message_post(
                    body=_(msg),
                    subject='%s' % msg, partner_ids=partn_ids, subtype_xmlid='mail.mt_comment', force_send=False)
                self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
            return


        #send email to the NOC team
        partn_ids = []
        user_names = ''
        intg_users = self.user_intg_ticket_group_id.sudo().user_ids

        for user in intg_users:
            if user.is_group_email:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

        if partn_ids:
            msg = 'The Ticket (%s) with description (%s), has been done by %s from the Engineering team' % (
                self.ticket_id, self.name, self.env.user.name)
            self.message_follower_ids.unlink()
            self.message_post(
                body=_(msg),
                subject='%s' % msg, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)
        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        # Send email to customer and sales person
        partner_id = self.partner_id
        if self.installation_date and partner_id and self.category_id == self.env.ref('fibernet.installation'):
            partner_id = self.partner_id
            installation_date = self.installation_date.strftime('%d/%m/%Y')

            if not partner_id.email:
                raise UserError(
                    'Kindly set the email for the %s with client id %s, in the customers database' % (
                        partner_id.name, partner_id.ref or ''))

            msg = 'Dear %s, <p>We are delighted to inform you that your installation with Ticket ID (%s) has been successfully completed by %s from the Technical team and is now awaiting activation. </p> <p> We understand the importance of getting your internet service up and running as soon as possible, and we assure you that we are working diligently to expedite the activation process. We will keep you informed and provide regular updates regarding the status of your activation.</p><p> Regards,</p><p>Customer Onboarding/Retention Center</p>' % \
                  (
                      partner_id.name, self.ticket_id, self.installation_fse_id.name)
            self.message_follower_ids.unlink()
            mail_obj = self.message_post(
                body=_(msg),
                subject='%s Completed Installation Ticket Notification for %s' % (
                    self.sudo().product_id.name, partner_id.name), partner_ids=[partner_id.id],
                subtype_xmlid='mail.mt_comment', force_send=False)
            user_names += partner_id.name + ", "
            mail_obj.email_from = 'csc@fibernet.ng'
            mail_obj.reply_to = 'csc@fibernet.ng'

            # notify sales person
            if self.sudo().order_id.user_id:
                subject = 'For your information. Installation for %s, which was scheduled on %s , has been installed by %s' % (
                self.partner_id.name, installation_date, self.installation_fse_id.name)
                smsg = "<p> Dear %s </p><p> Kindly see the message below for your reference </p> <br />" % self.sudo().order_id.user_id.name
                self._send_email_to_sales_person(subject, smsg + msg)

                # send email to other authorized group
                self.send_email('fibernet.group_ticket_installation_date_notify',
                                subject=subject,
                                msg=smsg + msg)

        return super(Ticket,self).btn_ticket_done()


    def create_customer_contract(self):
        sale_order = self.order_id
        package = sale_order.order_line.filtered(lambda line: line.product_id.is_sub == True)
        self.contract_id = self.env['contract.contract'].create(
            {
                'name' : sale_order.partner_id.name,
                'partner_id' : sale_order.partner_id.id,
                'payment_term_id' : sale_order.payment_term_id.id,
                'date_start': self.activation_date,
                'recurring_next_date': self.activation_date + relativedelta(days=23),
                'next_due_date': self.activation_date + relativedelta(days=30),
                'contract_line_fixed_ids': [(0, 0, {
                    'product_id': package.mapped('product_id')[0].id,
                    'name': package.mapped('name')[0],
                    'quantity': package.mapped('product_uom_qty')[0],
                    'uom_id':  package.mapped('product_uom')[0].id,
                    'price_unit': package.mapped('price_unit')[0],
                     'date_start': self.activation_date,
                    'recurring_next_date': self.activation_date + relativedelta(days=23),
                })],
            }
        )



    def btn_ticket_close(self):

        if self.category_id == self.env.ref('fibernet.installation') and self.state != 'finalized' :
            raise UserError('You cannot close an installation ticket that is not yet finalized')

        if self.category_id == self.env.ref('fibernet.installation') and self.order_id :
            self.sudo().order_id.is_installation_ticket_close = True

            #set partner parameters
            self.partner_id.status = self.status
            self.partner_id.activation_date = self.activation_date

            #create invoice
            if self.order_id :
                if self.invoice_id :
                    raise UserError('Sorry, this ticket has been previously closed and invoice created. Please refresh your browser')
                invoice = self.create_customer_invoice(self.order_id)
                contract = self.create_customer_contract()

            # send email
            self.send_email('fibernet.group_ticket_installation_close_notify',subject='An Installation Ticket has been closed',
            msg = _('The Installation Ticket %s has been closed for the order id - %s, from %s') % (
                self.name, self.sudo().order_id.name, self.env.user.name))


            # Send email to the customer for closing the installation ticket
            partner_id = self.partner_id
            user_names = ''
            if partner_id:
                if not partner_id.email :
                    raise UserError('Kindly set the email for %s with client id %s, in the customers database, before this ticket can be closed' % (partner_id.name, partner_id.ref or ''))

                msg = 'Dear %s, <p>This is to notify you that we have completed and closed the process of installing your package - %s. An installation ticket with the ID: %s has been completed and closed.  </p> <p>Thanks for your patronage. We hope you enjoy the service</p><p>Regards</p>' % (
                    self.partner_id.name, self.sudo().product_id.name, self.ticket_id)
                self.message_follower_ids.unlink()
                mail_obj = self.message_post(
                    body=_(msg),
                    subject='%s Completed and Closed Installation Ticket Notification for %s' % (self.sudo().product_id.name, partner_id.name), partner_ids=[partner_id.id],subtype_xmlid='mail.mt_comment', force_send=False)
                user_names += partner_id.name + ", "
                mail_obj.email_from = 'csc@fibernet.ng'
                mail_obj.reply_to = 'csc@fibernet.ng'

                self.env.user.notify_info('%s Will Be Notified by Email for Installation Ticket Closure' % (user_names))

        elif self.category_id == self.env.ref('fibernet.support') :
            # Send email to the customer for closing the support ticket
            partner_id = self.partner_id
            user_names = ''
            if partner_id:
                msg = 'Dear %s, <p>This is to notify you that we have resolved the complaint for your package %s with ticket ID: %s.  </p> <p>Thanks for your patronage. We hope you enjoy the service</p><p>Regards</p>' % (
                    self.partner_id.name, self.sudo().product_id.name, self.ticket_id)
                self.message_follower_ids.unlink()
                mail_obj = self.message_post(
                    body=_(msg),
                    subject='%s Support Ticket Closed Notification for %s' % (
                    self.sudo().product_id.name, partner_id.name), partner_ids=[partner_id.id],
                    subtype_xmlid='mail.mt_comment', force_send=False)
                user_names += partner_id.name + ", "
                mail_obj.email_from = 'csc@fibernet.ng'
                mail_obj.reply_to = 'csc@fibernet.ng'
                self.env.user.notify_info('%s Will Be Notified by Email for Installation Ticket Closure' % (user_names))

        elif self.category_id == self.env.ref('fibernet.survey') :
            # send email
            self.send_email('fibernet.group_ticket_survey_close_notify',
                            subject='The Survey Ticket has been closed',
                            msg=_(
                                'The Survey Ticket %s has been closed for the order id - %s, from %s') % (
                                    self.name, self.sudo().order_id.name, self.env.user.name))


        elif self.category_id == self.env.ref('fibernet.updown_grade'):
            # send email
            self.send_email('fibernet.group_ticket_updown_close_notify',
                            subject='The Change Request Ticket has been closed',
                            msg=_(
                    'The Change Request Ticket %s has been closed by %s') % (
                    self.name,self.env.user.name))

        return super(Ticket,self).btn_ticket_close()


    def action_ticket_opener_reject(self, msg):
        self.state = 'progress'
        self.opener_disapprove_by = self.env.user
        self.opener_disapprove_date = datetime.today()
        self.opener_disapprove_msg = msg

        if self.category_id == self.env.ref('fibernet.survey'):
            raise UserError(_("Sorry, This action is Not Necessary Surveys "))
        else:
            partn_ids = []
            user_names = ''
            mesg = 'The Ticket (%s) with description (%s), has been Rejected by %s with reason: (%s)' % (
                self.ticket_id, self.name, self.env.user.name, msg)

            init_users = self.initiator_ticket_group_id.sudo().user_ids
            for user in init_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

            assign_users = self.user_ticket_group_id.sudo().user_ids
            for user in assign_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

            if partn_ids:
                self.message_follower_ids.unlink()
                self.message_post(
                    body=_(mesg),
                    subject='%s' % mesg, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)

            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))


    def _send_debt_email_to_sales_person(self,debt_subject,debt_msg):
        # Send email to sales person
        partn_ids = []
        user = self.order_id.user_id
        user_name = user.name
        partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.order_id.message_follower_ids.unlink()
            self.order_id.message_post(
                body=debt_msg,
                subject=debt_subject, partner_ids=partn_ids,
                subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_danger(debt_msg,sticky=True,title='Debt Notification Alert')

    def _send_debt_email_to_csc(self,debt_subject,debt_msg):
        partn_ids = []
        user_names = ''
        ope_users = self.initiator_ticket_group_id.sudo().user_ids
        for user in ope_users:
            if user.is_group_email:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_follower_ids.unlink()
            self.message_post(
                body=_(debt_msg),
                subject=debt_subject, partner_ids=partn_ids, subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

    def btn_ticket_finalized(self):

        if self.partner_id and self.category_id == self.env.ref('fibernet.installation'):
            if not self.ip_address:
                raise UserError(_('Please set the Customer IP Address in the Activation Form Tab below'))

            if not self.gpon_level:
                raise UserError(_('Please set the GPON Port in the Activation Form Tab below'))

            if not self.activation_date :
                raise UserError('Please set the activation date for this service in the activation tab below')

            if not self.expiration_date :
                raise UserError('Please set the expiration date for this service in the activation tab below')

            #push new customer to selfcare
            if not self.order_id :
                raise UserError('No Sales Order for this Ticket')

            if self.order_id.amount_balance and self.order_id.amount_balance > 0:
                debt_subject = '%s has a balance of %s%s, to pay before his account can be activated, for the sales order (%s)' % (self.partner_id.name, self.order_id.currency_id.symbol, self.order_id.amount_balance, self.order_id.name)
                debt_msg = '%s has a balance of %s%s, to pay before his account can be activated.  %s should request for the balance payment and contact the accountant to approve the sales order (%s) with the balance before you can re-try finalizing this ticket '% (self.partner_id.name, self.order_id.currency_id.symbol, self.order_id.amount_balance,self.order_id.user_id.name, self.order_id.name)
                #notify the sales person
                self._send_debt_email_to_sales_person(debt_subject,debt_msg)

                #notify csc
                self._send_debt_email_to_csc(debt_subject,debt_msg)
                self.alert_msg = debt_msg
                self.show_alert_box = True
                return
            else:
                self.alert_msg = ''
                self.show_alert_box = False
                self.state = 'finalized'
                self.finalized_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            mrc_subscription = self.order_id.order_line.filtered(lambda line: line.product_id.is_sub == True)
            self.partner_id.amount = mrc_subscription.price_unit
            self.partner_id.action_create_customer_selfcare()
            self.partner_id.action_create_customer_eservice()

            self.partner_id.status = 'active'
            #self.partner_id.activation_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            # Send email to the customer after activation from NOC for the installation ticket
            user_names = ''
            if self.partner_id and self.partner_id.email:
                msg = '<p>Dear %s, (ID %s) </p> <p>We, at Fibernet, are honored to have you as one of our reputable customers. </p> <p> Your account has been activated and we are confident that you will be very satisfied with our services. Find below details of your service portal login from which you can manage your account.</p> <p> Client ID: %s <br/> Service Plan: %s </p>   <p>You can manage your service via the platform below;<br/>Fibernet Self-service Portal - <a href= https://selfcare.fibernet.ng/ > https://selfcare.fibernet.ng/</a> <br/>Username : %s<br/>Password : %s</p> <p><b>Contact Us</b><br/>You can contact our customer service center via the following platforms. <ul><li> Email: csc@fibernet.ng,support@fibernet.ng</li><li>Phone:+2349083301363 </li><li>Whatsapp: +2349071011409</li><li>Website online chat via: <a href= http://www.fibernet.ng > http://www.fibernet.ng</a>  </li></ul> </p> <p><b>Service Renewal:</b><br/>You can renew your service via our automated platform.<br/> Fibernet Self-care Portal - <a href= https://selfcare.fibernet.ng/ > https://selfcare.fibernet.ng/</a></p> <p> Thank you again for your business.</p> <p> Sincerely, </p> <p><b> Customer Service Center </b> </p>' % (
                    self.partner_id.name, self.partner_id.ref, self.partner_id.ref, self.product_id.name, self.partner_id.ref, self.partner_id.ref)
                mail_obj = self.message_post(body=_(msg), subject='%s - Welcome to Fibernet Broadband' % (self.partner_id.name),
                                             partner_ids=[self.partner_id.id], subtype_xmlid='mail.mt_comment', force_send=False)
                user_names += self.partner_id.name + ", "
                mail_obj.email_from = 'csc@fibernet.ng'
                mail_obj.reply_to = 'csc@fibernet.ng'
        elif self.partner_id and self.category_id == self.env.ref('fibernet.updown_grade'):
            self.state = 'finalized'
            self.finalized_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        # email ticket opener users
        partn_ids = []
        user_names = ''
        msg = 'The Ticket (%s) with description (%s), has been finalized by %s from the finalized team, you may now close the ticket' % (
            self.ticket_id, self.name, self.env.user.name)

        ope_users = self.initiator_ticket_group_id.sudo().user_ids
        for user in ope_users:
            if user.is_group_email:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_follower_ids.unlink()
            self.message_post(
                body=_(msg),
                subject='%s' % msg, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))



    #finalized rejection
    def action_ticket_reject(self,msg):
        self.state = 'progress'
        self.finalized_reject_by = self.env.user
        self.finalized_rejection_date = datetime.today()
        self.finalized_reject_msg = msg

        #send email to the assigned user group
        partn_ids = []
        user_names = ''
        assign_users = self.user_ticket_group_id.sudo().user_ids
        subject = 'The Ticket (%s) with description (%s), has been Dis-approved by %s, from the Integration team, with reason: (%s)' % (
            self.ticket_id, self.name, self.env.user.name, msg)
        for user in assign_users:
            if user.is_group_email:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_follower_ids.unlink()
            self.message_post(
                body=_(msg),
                subject='%s' % msg, partner_ids=partn_ids, subtype_xmlid='mail.mt_comment', force_send=False)
        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))


    def get_default_eng_group(self):
        res = self.env['user.ticket.group'].search([('is_eng_default','=',True)],limit=1)
        return res


    def get_default_intg_group(self):
        res = self.env['user.ticket.group'].search([('is_intg_default','=',True)],limit=1)
        return res

    def get_initiator_group(self):
        res = self.env['user.ticket.group'].search([('user_ids', '=', self.env.user.id)],limit=1)
        return res


    def write(self,vals):
        if self.partner_id and self.category_id == self.env.ref('fibernet.installation') :
            area_id = vals.get('area_customer_id', False)
            if area_id and not self.partner_id.ref:
                if self.order_id.client_type == 'corporate':
                    vals['ref'] = self.env['ir.sequence'].next_by_code('cust_cid_code')
                else:
                    sequence_id = self.env['area'].browse(area_id).sequence_id
                    if sequence_id:
                        vals['ref'] = sequence_id.next_by_id()
                    else:
                        vals['ref'] = ''

            cust_vals = {
                'location_id' : vals.get('location_id',self.partner_id.location_id),
                'region_id' : vals.get('region_cust_id',self.partner_id.region_id),
                'area_id': vals.get('area_customer_id', self.partner_id.area_id),
                'base_station_id': vals.get('base_station_id', self.partner_id.base_station_id),
                'bandwidth': vals.get('bandwidth', self.partner_id.bandwidth),
                'vlan': vals.get('vlan', self.partner_id.vlan),
                'contact_person': vals.get('contact_person', self.partner_id.contact_person),
                'cpe': vals.get('cpe', self.partner_id.cpe),
                'ip_address': vals.get('ip_address', self.partner_id.ip_address),
                'radio_ip_address': vals.get('radio_ip_address', self.partner_id.radio_ip_address),
                'base_station_ip_address': vals.get('base_station_ip_address', self.partner_id.base_station_ip_address),
                'subnet': vals.get('subnet', self.partner_id.subnet),
                'gateway': vals.get('gateway', self.partner_id.gateway),
                'indoor_wan': vals.get('indoor_wan', self.partner_id.indoor_wan),
                'comment': vals.get('comment', self.partner_id.comment),
                'activation_date': vals.get('activation_date', self.partner_id.activation_date),
                'reg_date': vals.get('reg_date', self.partner_id.reg_date),
                'last_logoff': vals.get('last_logoff', self.partner_id.last_logoff),
                'gpon': vals.get('gpon_level', self.partner_id.gpon),
                'interface': vals.get('interface', self.partner_id.interface),
                'serial_no': vals.get('idu_serial_no', self.partner_id.serial_no),
                'product_id': vals.get('product_id', self.partner_id.product_id),
                'olt_id' : vals.get('olt_id', self.partner_id.olt_id),
                'status' : vals.get('status', self.partner_id.status),
                'installation_fse_id': vals.get('installation_fse_id', self.partner_id.installation_fse_id),
                'power_level_id': vals.get('power_level_id', self.partner_id.power_level_id),
                'ref' : vals.get('ref', self.partner_id.ref),
                'expiration_date' : vals.get('expiration_date', self.partner_id.expiration_date),
           }
            self.partner_id.write(cust_vals)

        #  #update the change request new values
        if self.state == 'closed' and self.category_id == self.env.ref('fibernet.updown_grade'):
            self.partner_id.product_id = self.product_new_id
            self.partner_id.bandwidth = self.bandwidth_new
            self.partner_id.street = self.address_new
            self.partner_id.ip_address = self.adddress_ip_new
            self.partner_id.serial_no = self.serial_new
            self.partner_id.gpon = self.gpon_new
            self.partner_id.power_level_id = self.power_level_new_id

        #reassign ticket notification
        assigned_users = vals.get('user_ticket_group_id', False)
        if self.state in ('new', 'progress') and assigned_users:
            # send email
            partn_ids = []
            user_names = ''
            assign_users = self.user_ticket_group_id.sudo().user_ids
            msg = 'The Ticket (%s) with description (%s), has been re-assigned to %s, by %s' % (
                self.ticket_id, self.name, self.user_ticket_group_id.name, self.env.user.name)
            for user in assign_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

            if partn_ids:
                self.message_follower_ids.unlink()
                self.message_post(
                    body=_(msg),
                    subject='%s' % msg, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)
                self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
        return super(Ticket, self).write(vals)

    @api.onchange('movement_type')
    def _compute_installation_cost(self):
        installation_cost_mobilized = self.env['ir.config_parameter'].sudo().get_param('fibernet.installation_cost_mobilized')
        installation_cost_not_mobilized = self.env['ir.config_parameter'].sudo().get_param('fibernet.installation_cost_not_mobilized')

        if self.movement_type == 'mobilized' :
            self.installation_cost = installation_cost_mobilized
        elif self.movement_type == 'not mobilized' :
            self.installation_cost = installation_cost_not_mobilized

    @api.onchange('cable_used_meter')
    def _compute_cabling_price(self):
        cable_cost = self.env['ir.config_parameter'].sudo().get_param('fibernet.cable_cost')
        if self.cable_used_meter > 0 :
            self.cabling_price = self.cable_used_meter * float(cable_cost)
        else:
            self.cabling_price = 0

    @api.onchange('ladder_amt','installation_cost')
    def _compute_total_amt(self):
        self.total_amt = self.ladder_amt + self.installation_cost



    #remove store=True for the related fields, because it prevents the helpdesk user from saving a ticket with partner information if there are other tickets attached to the partner, and the user is not in the group for all the previous tickets attached to the partner. so the helpdesk user rule prevents it from saving the form for the related fields with store parameter, since it will want to update the partner which inturns update all other previous tickets having the store=True paramter ( I have tested the fact  the system updates other previous tickets indirectly, whne given the  Helpdesk general manager rights which have access to all tickets)
    cust_name = fields.Char(related='partner_id.name', string='Name', readonly=True)
    street = fields.Char(related='partner_id.street', string='Address', readonly=True)
    website = fields.Char(related='partner_id.website', string='Website', readonly=True)
    company_id = fields.Many2one(related='partner_id.company_id', string='Company', readonly=True)
    ref = fields.Char(related='partner_id.ref', string='Client ID', readonly=True, states={'done': [('readonly', False)]})
    location_id = fields.Many2one(related='partner_id.location_id', string='Location')
    region_cust_id = fields.Many2one(related='partner_id.region_id', string='Region')
    area_customer_id = fields.Many2one(related='partner_id.area_id', string='Area')
    base_station_id = fields.Many2one(related='partner_id.base_station_id', string='Base Station')
    bandwidth = fields.Char(related='partner_id.bandwidth', string='Bandwidth')
    vlan = fields.Char(related='partner_id.vlan', string='Vlan')
    contact_person = fields.Char(related='partner_id.contact_person', string='Contact Person')
    cpe = fields.Char(related='partner_id.cpe', string='CPE Model')
    ip_address = fields.Char(related='partner_id.ip_address', string='Customer IP Address')
    radio_ip_address = fields.Char(related='partner_id.radio_ip_address', string='Radio IP Address')
    base_station_ip_address = fields.Char(related='partner_id.base_station_ip_address', string='Base Station IP Address')
    subnet = fields.Char(related='partner_id.subnet',string='Subnet')
    gateway = fields.Char(related='partner_id.gateway',string='Gateway')
    indoor_wan = fields.Char(related='partner_id.indoor_wan',string='Indoor WAN IP Address')
    comment = fields.Char(related='partner_id.comment', string='Comment')
    activation_date = fields.Date(related='partner_id.activation_date',string='Activation Date')
    status = fields.Selection(related='partner_id.status',string='Status')
    function = fields.Char(related='partner_id.function', string='Job Position', readonly=True)
    phone = fields.Char(related='partner_id.phone', string='Phone', readonly=True)
    mobile = fields.Char(related='partner_id.mobile', string='Mobile', readonly=True)
    email = fields.Char(related='partner_id.email', string='Email', readonly=True)


    order_id = fields.Many2one('sale.order', string='Order')
    order_count = fields.Integer(compute="_compute_order_count", string='# of Order(s)', copy=False, default=0)
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_count = fields.Integer(compute="_compute_invoice_count", string='# of Invoices', copy=False, default=0)
    contract_id = fields.Many2one('contract.contract', string='Contract')
    contract_count = fields.Integer(compute="_compute_contract_count", string='# of Contract', copy=False, default=0)

    title = fields.Many2one(related='partner_id.title',string="Title", readonly=True)
    gender = fields.Selection(related='partner_id.gender',  string='Gender', readonly=True)    
    estate_id = fields.Many2one(related='partner_id.estate_id',string='Estate', readonly=True)
    city_cust = fields.Char(related='partner_id.city_cust',string='City', readonly=True)  
    dob = fields.Date(related='partner_id.dob',string="DOB", readonly=True)
    state_ng = fields.Selection(related='partner_id.state_ng',string="State", readonly=True)

    expiration_date = fields.Date(related='partner_id.expiration_date',string="Expiration Date")
    reg_date = fields.Date(related='partner_id.reg_date', string="REG Date")
    last_logoff = fields.Date(related='partner_id.last_logoff', string="Last Logoff")
    gpon = fields.Char(related='partner_id.gpon', string="GPON")
    interface = fields.Char(related='partner_id.interface', string="Interface")
    serial_no = fields.Char(related='partner_id.serial_no', string="Serial No")

    #survey_ticket_id = fields.Many2one('kin.ticket',string='Site Survey Ticket')
    product_id = fields.Many2one(related='partner_id.product_id',string='Package')
    installation_form = fields.Binary(string='Installation Picture', attachment=True)
    rejection_evidence = fields.Binary(string='Rejection Evidence')


    root_cause = fields.Text(string='Root Cause')
    resolution = fields.Text(string='Resolution')
    call_type_support = fields.Selection([('inbound_support', 'Inbound Support'), ('inbound_enquiry', 'Inbound Enquiry'),
                                  ('outbound_retention', 'Outbound Retention')], string='Support Call Type')
    source_support = fields.Selection(
        [('call', 'Call'), ('email', 'Email'),
         ('chat', 'Chat'),('web', 'Web')], string='Source')
    complaint_type_support_id = fields.Many2one('complaint.type', string='Complaint Type')
    amt_support_expenses = fields.Integer(string="Engr. Amount Expenses")
    done_ticket_date = fields.Datetime(string='Resolved Ticket Date')


    opener_disapprove_msg = fields.Text(string='Ticket Opener Rejection Reason')
    opener_disapprove_by = fields.Many2one('res.users', string='Rejected By')
    opener_disapprove_date = fields.Datetime(string='Rejection Date and Time')

    finalized_reject_msg = fields.Text(string='Finalized Rejection Reason')
    finalized_reject_by = fields.Many2one('res.users',string='Rejected By')
    finalized_rejection_date = fields.Datetime(string='Rejection Date and Time')
    user_intg_ticket_group_id = fields.Many2one('user.ticket.group',default=get_default_intg_group, string='Finalized User Group',ondelete='restrict')
    initiator_ticket_group_id = fields.Many2one('user.ticket.group',default=get_initiator_group,string='Ticket Opener Group')
    user_ticket_group_id = fields.Many2one('user.ticket.group', default=get_default_eng_group, string='Assigned User Group')


    state = fields.Selection(
        [('draft', 'Draft'), ('new', 'Open'),  ('progress', 'Work In Progress'),('done', 'Completed'), ('finalized','Finalized'),('closed', 'Closed'),('cancel', 'Cancelled'),('archived', 'Archived')],
        default='draft', tracking=True)

    description = fields.Text(string='Incident Details')

    #Survey Form fields
    feasibility = fields.Selection([('feasible','Feasible'),('not_feasible','Not Feasible')], string='Feasibility')
    dist_fpop = fields.Char(string='Distance to FPOP / JB')
    fpop_box_jb = fields.Char(string='FPOP Box / JB')
    comment_survey = fields.Text(string='Comment')

    duration_close = fields.Char(string='Duration', compute=_compute_close_duration,store=True)

    #activation form
    olt_id = fields.Many2one(related='partner_id.olt_id',  string='OLT')
    gpon_level = fields.Char(related='partner_id.gpon',string='GPON Port')
    power_level_id = fields.Many2one(related='partner_id.power_level_id',string='Power Level')
    idu_serial_no = fields.Char(related='partner_id.serial_no',string='IDU SerialNumber')
    wifi_ssid = fields.Char(string='Wifi SSID')
    splitter_box_code = fields.Char(string='Splitter Box Code')
    region_id = fields.Many2one(related='partner_id.region_id', string='Region')
    installation_fse_id = fields.Many2one(related='partner_id.installation_fse_id',string='Installation FSE')
    installation_approver_id = fields.Many2one('res.users',string='Installation Approval')
    wireless_technology = fields.Char(string='Wireless Technology')
    rssi_id = fields.Char(string='RSSI')
    radio_ip_addr = fields.Char(string='Radio IP Address')
    indoor_ip_address = fields.Char(string='Indoor IP Address')
    ap_ip_address = fields.Char(string='AP IP Address')
    radio_model = fields.Char(string='Radio Model(microwave,MK,UB,Vjjt etc)')
    comment_activation = fields.Char(string='Comment')



    # Request
    prospect_name = fields.Char(string='Prospect Name')
    prospect_address = fields.Char(string='Prospect Address')
    prospect_area_id = fields.Many2one('area',string='Prospect Area')
    prospect_email = fields.Char(string='Prospect Email')
    prospect_phone = fields.Char(string='Prospect Phone')
    prospect_id = fields.Many2one('prospect', string ='Prospect')
    others_sales_person_id = fields.Many2one('res.users',string='Sales Person')
    is_others = fields.Boolean(related='prospect_area_id.is_others',string="Is Others")

    #Change Request
    area_change_request_id = fields.Many2one('area', string="New Area", tracking=True)
    updown_grade_type = fields.Selection([('relocation', 'Relocation'), ('upgrade', 'Upgrade'), ('downgrade', 'Downgrade'),('hold', 'Hold Subscription'),('reconnect', 'Reconnect'),('change_password', 'Change Password')], string='Change Request Type', tracking=True)
    product_curr_id = fields.Many2one('product.product',string='Current Package', tracking=True)
    product_new_id = fields.Many2one('product.product', string='New Package', tracking=True)
    bandwidth_current = fields.Char(string='Current Bandwidth', tracking=True)
    bandwidth_new = fields.Char(string='New Bandwidth', tracking=True)
    address_old = fields.Char(string='Old Address', tracking=True)
    address_new = fields.Char(string='New Address', tracking=True)
    address_ip_current = fields.Char(string='Current IP Address', tracking=True)
    adddress_ip_new = fields.Char(string='New IP Address', tracking=True)
    password_new = fields.Char(string='New Password', tracking=True)
    serial_new = fields.Char(string='New Serial No.', tracking=True)
    gpon_new = fields.Char(string='New GPON', tracking=True)
    power_level_new_id = fields.Many2one('pl', string='New Power Level', tracking=True)
    date_held = fields.Date(string='Date held', tracking=True)

    done_date = fields.Datetime(string='Completed Date')
    finalized_date = fields.Datetime(string='Finalized Date')
    installation_date = fields.Date(string='Installation Date', tracking=True)
    support_date = fields.Date(string='Support Date', tracking=True)

    last_log_datetime = fields.Datetime(string='Last Logged datetime')
    last_log_user_id = fields.Many2one('res.users',string='Last Logged User')
    last_log_message = fields.Html(string='Last Log Message')
    category_code = fields.Char(related='category_id.code', string='Category Code')

    assigned_eng_user_ids = fields.Many2many(related='user_ticket_group_id.user_ids', string='Engineers')
    show_alert_box = fields.Boolean(string="Show Alert Box")
    alert_msg = fields.Char(string='Alert Message')

    expiry_date = fields.Datetime(string='Expiry Date', tracking=True)
    is_escalation_email_sent = fields.Boolean(string='Is Escalation Email Sent', default=False, tracking=True)
    is_escalation_email_sent_date = fields.Datetime(string='Escalation Email Sent Date')

    installation_fee = fields.Float(string='Installation Fee')
    movement_type = fields.Selection([('mobilized', 'Mobilized'), ('not mobilized', 'Not Mobilized')], string='Movement Type', tracking=True)
    rent_ladder = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Rent ladder', tracking=True)
    ladder_amt = fields.Float(string="Ladder Price",tracking=True)
    cable_used = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Cable Used', tracking=True)
    cable_used_meter = fields.Float(string="Meter of Cable Used",tracking=True)
    cable_type = fields.Selection([('1 core','1 Core'), ('2 core','2 Core'),('4 core','4 Core'),('8 core','8 Core'),('12 core','12 Core'),('24 core','24 Core')],string='Cable Type', tracking=True)
    cabling_price = fields.Float(string="Cabling Price")
    onu_changed = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='ONU changed', tracking=True)
    old_serial_number = fields.Float(string="Old Serial Number",tracking=True)
    new_serial_number = fields.Float(string="New Serial Number",tracking=True)
    installation_cost = fields.Float(string='Installation Cost',tracking=True)
    patchcord_used = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Patch cord Used', tracking=True)
    patchcord_used_amt = fields.Float(string="Patch Cord Used Amt.",tracking=True)
    coppler_used = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Coppler Used', tracking=True)
    coppler_used_amt = fields.Float(string="Coppler Used Amt.",tracking=True)
    pigtail_used = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Pigtail Used', tracking=True)
    pigtail_used_amt = fields.Float(string="Pigtail Used Amt.",tracking=True)
    box_used = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Box Used', tracking=True)
    box_used_type = fields.Selection([('1 by 2','1 by 2'),('1 by 16','1 by 16')],string="Box Used Type",tracking=True)
    splitter_used = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Splitter Used', tracking=True)
    splitter_used_type = fields.Selection([('1 by 2','1 by 2'), ('1 by 4','1 by 4'), ('1 by 8','1 by 8')], string="Box Used Type",tracking=True)
    faceplate_used = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Faceplate Used', tracking=True)
    faceplate_used_amt = fields.Float(string="Faceplate Used Amt.", tracking=True)
    total_amt = fields.Float(string="Total Amt.")

class AccountInvoice(models.Model):
    _inherit = 'account.move'
    #
    # 
    # def write(self, vals):
    #     is_partner = vals.get('partner_id', False)
    #     if is_partner and self.is_advance_invoice:
    #         raise UserError(_('Sorry, you are not allowed to change the customer, for the advance payment invoice'))
    #
    #     res = super(AccountInvoice, self).write(vals)
    #     return res

    
    # def unlink(self):
    #     for rec in self:
    #         if rec.is_installation_invoice :
    #             if self.env.user not in rec.installation_ticket_id.initiator_ticket_group_id.sudo().user_ids:
    #                 raise UserError('Sorry, you cannot delete an installation invoice')
    #     return super(AccountInvoice,self).unlink()

    is_installation_invoice = fields.Boolean(string='Is Installation Invoice')
    installation_ticket_id = fields.Many2one('kin.ticket',string='Installation Ticket')


class Message(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, values):
        model = values.get('model', False)
        res = super(Message,self).create(values)
        if isinstance(model, bool):
            return res
        if 'kin.ticket' in values['model']:
            res_id = values['res_id']
            ticket_obj = self.env['kin.ticket'].browse(res_id)
            ticket_obj.last_log_datetime = datetime.today()
            ticket_obj.last_log_user_id = ticket_obj.env.user
            ticket_obj.last_log_message = values['body']
        return res