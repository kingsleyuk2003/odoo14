# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from datetime import datetime,date, timedelta
from odoo import api, fields, models, _
from urllib import urlencode
from urlparse import urljoin
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare,float_round, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz

class UserGroups(models.Model):
    _inherit = 'user.ticket.group'

    is_eng_default = fields.Boolean(string='Is Assigned Team Default')
    is_qa_default = fields.Boolean(string='Is QA Default')
    is_intg_default = fields.Boolean(string='Is Integration Default')
    is_survey_group_default_csc_fob = fields.Boolean(string='Is Survey Group Default for CSC FOB')
    is_survey_group_default_csc_kkon = fields.Boolean(string='Is Survey Group Default for CSC KKON')
    is_installation_group_default_csc_fob = fields.Boolean(string='Is Installation Group Default for CSC FOB')
    is_installation_group_default_csc_kkon = fields.Boolean(string='Is Installation Group Default for CSC KKON')
    is_maint_default = fields.Boolean(string='Is Maintenance Close Team Default')
    is_csc_kkon_group = fields.Boolean(string='Is CSC KKON Group')
    is_csc_fob_group = fields.Boolean(string='Is CSC FOB Group')

    is_bpsq_cto_manager = fields.Boolean(string='Is BPSQ/CTO')
    is_bpsq_md_manager = fields.Boolean(string='Is MD/BPSQ')
    is_regional_manager_hcx = fields.Boolean(string='Is Regional Manager/HCX')
    is_cto_rm_hcx = fields.Boolean(string='Is CTO/RM/HCX')
    is_hcx = fields.Boolean(string='Is HCX')
    is_hcx_team_lead = fields.Boolean(string='Is HCX/Teamlead')
    is_cx = fields.Boolean(string='Is CX')
    is_team_lead = fields.Boolean(string='Is Teamlead')
    is_bpsq_hcx = fields.Boolean(string='Is BPSQ/HCX')


class Estate(models.Model):
    _name = "kkon.estate"

    name = fields.Char(string='Estate')

class OLT(models.Model):
    _name = "kkon.olt"

    name = fields.Char(string='OLT')


class PowerLevel(models.Model):
    _name = "kkon.pl"

    name = fields.Char(string='Power Level')

class REGION(models.Model):
    _name = "kkon.region"

    name = fields.Char(string='Region')

class Area(models.Model):
    _name = "kkon.area"

    name = fields.Char(string='Area')
    area_manager_id = fields.Many2one('res.users',string="Area Manager")

class CompliantType(models.Model):
    _name = "kkon.complaint.type"

    name = fields.Char(string='Compliant Type')

class RSSI(models.Model):
    _name = "kkon.rssi"

    name = fields.Char(string='RSSI')

class ElapsedHoursFirst(models.Model):
    _name = "kkon.elapsed.hour.first"

    day_no = fields.Integer(string="Day No.")
    elapsed_hours = fields.Integer(string="Elapsed Hours")
    ticket_id = fields.Many2one('kin.ticket',  string='Ticket')



class ElapsedHoursSecond(models.Model):
    _name = "kkon.elapsed.hour.second"

    day_no = fields.Integer(string="Day No.")
    elapsed_hours = fields.Integer(string="Elapsed Hours")
    ticket_id = fields.Many2one('kin.ticket',  string='Ticket')


class ElapsedHoursThird(models.Model):
    _name = "kkon.elapsed.hour.third"

    day_no = fields.Integer(string="Day No.")
    elapsed_hours = fields.Integer(string="Elapsed Hours")
    ticket_id = fields.Many2one('kin.ticket',  string='Ticket')

class Ticket(models.Model):
    _inherit = 'kin.ticket'
    _rec_name = 'ticket_id'


    def send_escalation_msg(self,partner_ids,subject,msg):
        if partner_ids:
            self.message_post(msg, subject=subject, partner_ids=partner_ids, subtype_xmlid='mail.mt_comment', force_send=False)
        return

    def get_escalation_partners(self, user_type):
        partner_ids = []
        if user_type == "is_area_manager" :
            area = self.area_change_request_id
            if area :
                area_manager = area.area_manager_id
                if area_manager :
                    self.message_follower_ids.unlink()
                    partner_ids.append(area_manager.partner_id.id)
        else :
            user_ticket_group = self.env['user.ticket.group'].search([(user_type, '=', True)])
            if user_ticket_group:
                users = user_ticket_group[0].user_ids
                self.message_follower_ids.unlink()
                for user in users:
                    partner_ids.append(user.partner_id.id)
        return partner_ids


    def escalate_first(self,user_type,esc_type, hours):
        subject = False
        msg = False
        if self.open_date :
            user_tz_obj = pytz.timezone(self.env.context.get('tz') or 'Africa/Lagos')
            localize_tz = pytz.utc.localize
            open_date_format = localize_tz(datetime.strptime(self.open_date, '%Y-%m-%d %H:%M:%S')).astimezone(user_tz_obj).strftime('%d-%m-%Y %H:%M:%S')
            subject = 'Service Relocation Ticket Alert (%s) for ticket with ID: %s' % (esc_type, self.ticket_id)
            msg = _(
                'The is to bring to your attention, that the service relocation ticket (%s) with subject (%s), which was opened on %s, has not been closed. Kindly attend to the Service relocation ticket and ensure it is closed, to avoid further escalation') % (
                    self.ticket_id, self.name, open_date_format)

            partner_ids = self.get_escalation_partners(user_type)
            if subject and msg:
                self.send_escalation_msg(partner_ids, subject, msg)
        return subject, msg

    def escalate_second(self, user_type, esc_type, hours):
        subject = False
        msg = False
        if self.done_date:
            user_tz_obj = pytz.timezone(self.env.context.get('tz') or 'Africa/Lagos')
            localize_tz = pytz.utc.localize
            done_date_format = localize_tz(datetime.strptime(self.done_date, '%Y-%m-%d %H:%M:%S')).astimezone(
                user_tz_obj).strftime('%d-%m-%Y %H:%M:%S')
            subject = 'Completed Service Relocation Ticket Alert (%s) for ticket with ID: %s' % (esc_type, self.ticket_id)
            msg = _(
                'The is to bring to your attention, that the service relocation ticket (%s) with subject (%s), which has been completed on %s, has not been closed. Kindly attend to the Service relocation ticket and ensure it is closed, to avoid further escalation') % (
                      self.ticket_id, self.name, done_date_format)

            partner_ids = self.get_escalation_partners(user_type)
            if subject and msg:
                self.send_escalation_msg(partner_ids, subject, msg)
        return subject, msg

    def escalate_third(self, user_type, esc_type, hours):
        subject = False
        msg = False
        if self.integration_date:
            user_tz_obj = pytz.timezone(self.env.context.get('tz') or 'Africa/Lagos')
            localize_tz = pytz.utc.localize
            integration_date_format = localize_tz(datetime.strptime(self.integration_date, '%Y-%m-%d %H:%M:%S')).astimezone(
                user_tz_obj).strftime('%d-%m-%Y %H:%M:%S')
            subject = 'Finalized Service Relocation Ticket Alert (%s) for ticket with ID: %s' % (esc_type, self.ticket_id)
            msg = _(
                'The is to bring to your attention, that the service relocation ticket (%s) with subject (%s), which has been finalized on %s, has not been closed. Kindly attend to the Service relocation ticket and ensure it is closed, to avoid further escalation') % (
                      self.ticket_id, self.name, integration_date_format)

            partner_ids = self.get_escalation_partners(user_type)
            if subject and msg:
                self.send_escalation_msg(partner_ids, subject, msg)
        return subject, msg



    def escalate_first_service_relocation(self):
        today = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        tickets = self.search(
            [('open_date', '<', today), ('is_service_relocation', '=', 'yes'),
             ('state', 'not in', ['draft', 'closed'])])

        for ticket in tickets:
            total_elapsed_hours = ticket.total_elapsed_hours_first
            user_type = ''
            esc_type = ''
            hours = 0
            if total_elapsed_hours == 54:
                user_type = 'is_bpsq_md_manager'
                esc_type = 'EXTREMELY OVERDUE ESCALATION'
                hours = 54
            elif total_elapsed_hours == 41:
                user_type = 'is_bpsq_cto_manager'
                esc_type = 'OVERDUE ESCALATION'
                hours = 41
            elif total_elapsed_hours == 27:
                user_type = 'is_bpsq_cto_manager'
                esc_type = 'DUE ESCALATION'
                hours = 27
            elif total_elapsed_hours == 21:
                user_type = 'is_cto_rm_hcx'
                esc_type = 'HIGH ESCALATION'
                hours = 21
            elif total_elapsed_hours == 14:
                user_type = 'is_regional_manager_hcx'
                esc_type = 'MODERATE ESCALATION'
                hours = 14
            elif total_elapsed_hours == 7:
                user_type = 'is_area_manager'
                esc_type = 'NORMAL'
                hours = 7

            if user_type and esc_type and hours :
                ticket.escalate_first(user_type, esc_type, hours)



    def escalate_second_service_relocation(self):
        today = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        tickets = self.search(
            [('done_date', '<', today), ('is_service_relocation', '=', 'yes'),
             ('state', '=', 'done')])

        for ticket in tickets:
            total_elapsed_hours = ticket.total_elapsed_hours_second
            user_type = ''
            esc_type = ''
            hours = 0
            if total_elapsed_hours == 6:
                user_type = 'is_bpsq_md_manager'
                esc_type = 'EXTREMELY OVERDUE ESCALATION'
                hours = 6
            elif total_elapsed_hours == 4:
                user_type = 'is_hcx'
                esc_type = 'DUE ESCALATION'
                hours = 4
            elif total_elapsed_hours == 3:
                user_type = 'is_hcx_team_lead'
                esc_type = 'HIGH ESCALATION'
                hours = 3
            elif total_elapsed_hours == 2:
                user_type = 'is_hcx'
                esc_type = 'MODERATE ESCALATION'
                hours = 2
            elif total_elapsed_hours == 1:
                user_type = 'is_hcx'
                esc_type = 'NORMAL ESCALATION'
                hours = 1

            if user_type and esc_type and hours:
                ticket.escalate_second(user_type, esc_type, hours)


    def escalate_third_service_relocation(self):
        today = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        tickets = self.search(
            [('integration_date', '<', today), ('is_service_relocation', '=', 'yes'),
             ('state', '=', 'done')])

        for ticket in tickets:
            total_elapsed_hours = ticket.total_elapsed_hours_third
            user_type = ''
            esc_type = ''
            hours = 0
            if total_elapsed_hours == 12:
                user_type = 'is_bpsq_hcx'
                esc_type = 'HIGH ESCALATION'
                hours = 12
            elif total_elapsed_hours == 9:
                user_type = 'is_hcx'
                esc_type = 'HIGH ESCALATION'
                hours = 9
            elif total_elapsed_hours == 6:
                user_type = 'is_team_lead'
                esc_type = 'MODERATE ESCALATION'
                hours = 6
            elif total_elapsed_hours == 3:
                user_type = 'is_cx'
                esc_type = 'NORMAL ESCALATION'
                hours = 3

            if user_type and esc_type and hours:
                ticket.escalate_third(user_type, esc_type, hours)

    @api.depends('elapsed_hours_first')
    def _compute_total_elapsed_hours_first(self):
        for rec in self:
            total_elapsed_hours = 0
            for elh in rec.elapsed_hours_first:
                total_elapsed_hours += elh.elapsed_hours
            rec.total_elapsed_hours_first = total_elapsed_hours


    @api.depends('elapsed_hours_second')
    def _compute_total_elapsed_hours_second(self):
        for rec in self:
            total_elapsed_hours = 0
            for elh in rec.elapsed_hours_second:
                total_elapsed_hours += elh.elapsed_hours
            rec.total_elapsed_hours_second = total_elapsed_hours


    @api.depends('elapsed_hours_third')
    def _compute_total_elapsed_hours_third(self):
        for rec in self:
            total_elapsed_hours = 0
            for elh in rec.elapsed_hours_third:
                total_elapsed_hours += elh.elapsed_hours
            rec.total_elapsed_hours_third = total_elapsed_hours


    def update_elapsed_table_first(self, day_no, elapsed_hours):
        the_elapsed_rec = self.elapsed_hours_first.search([('day_no', '=', day_no),('ticket_id', '=', self.id)])
        if not the_elapsed_rec :
            self.elapsed_hours_first.create({'day_no': day_no, 'elapsed_hours': elapsed_hours, 'ticket_id': self.id})
        else :
            the_elapsed_rec.write({'elapsed_hours': elapsed_hours})

    def update_elapsed_table_second(self, day_no, elapsed_hours):
        the_elapsed_rec = self.elapsed_hours_second.search([('day_no', '=', day_no),('ticket_id', '=', self.id)])
        if not the_elapsed_rec :
            self.elapsed_hours_second.create({'day_no': day_no, 'elapsed_hours': elapsed_hours, 'ticket_id': self.id})
        else :
            the_elapsed_rec.write({'elapsed_hours': elapsed_hours})

    def update_elapsed_table_third(self, day_no, elapsed_hours):
        the_elapsed_rec = self.elapsed_hours_third.search([('day_no', '=', day_no),('ticket_id', '=', self.id)])
        if not the_elapsed_rec :
            self.elapsed_hours_third.create({'day_no': day_no, 'elapsed_hours': elapsed_hours, 'ticket_id': self.id})
        else :
            the_elapsed_rec.write({'elapsed_hours': elapsed_hours})


    def set_hours_elapsed(self,tickets,escalation_type):
        dtoday = datetime.today()
        tday = dtoday.day
        user_tz_obj = pytz.timezone(self.env.context.get('tz') or 'Africa/Lagos')
        localize_tz = pytz.utc.localize
        for ticket in tickets:
            start_day = False
            start_hour = False
            if escalation_type == 'first':
                start_day = localize_tz(
                    datetime.strptime(ticket.open_date, '%Y-%m-%d %H:%M:%S')).astimezone(
                    user_tz_obj).day
                start_hour = localize_tz(
                    datetime.strptime(ticket.open_date, '%Y-%m-%d %H:%M:%S')).astimezone(
                    user_tz_obj).hour
            elif escalation_type == 'second':
                start_day = localize_tz(
                    datetime.strptime(ticket.done_date, '%Y-%m-%d %H:%M:%S')).astimezone(
                    user_tz_obj).day
                start_hour = localize_tz(
                    datetime.strptime(ticket.done_date, '%Y-%m-%d %H:%M:%S')).astimezone(
                    user_tz_obj).hour
            elif escalation_type == 'third':
                start_day = localize_tz(
                    datetime.strptime(ticket.integration_date, '%Y-%m-%d %H:%M:%S')).astimezone(
                    user_tz_obj).day
                start_hour = localize_tz(
                    datetime.strptime(ticket.integration_date, '%Y-%m-%d %H:%M:%S')).astimezone(
                    user_tz_obj).hour

            day_no = tday - start_day + 1
            current_hour = dtoday.hour + 1

            is_sunday = False
            if dtoday.weekday() == 6 :
                is_sunday = True
            if 8 < current_hour < 18 and not is_sunday:
                current_hours_elapsed = current_hour - 8
                if day_no == 1:
                    if start_hour <= 8 :
                        start_hour = 8
                    current_hours_elapsed = current_hour - start_hour
                if escalation_type == 'first' :
                    ticket.update_elapsed_table_first(day_no, current_hours_elapsed)
                    ticket._compute_total_elapsed_hours_first()
                elif escalation_type == 'second' :
                    ticket.update_elapsed_table_second(day_no, current_hours_elapsed)
                    ticket._compute_total_elapsed_hours_second()
                elif escalation_type == 'third' :
                    ticket.update_elapsed_table_third(day_no, current_hours_elapsed)
                    ticket._compute_total_elapsed_hours_third()



    def set_hours_elapsed_first(self):
        today = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        tickets = self.search(
            [('open_date', '<', today), ('is_service_relocation', '=', 'yes'),
             ('state', 'not in', ['draft', 'closed'])])
        self.set_hours_elapsed(tickets,'first')

    def set_hours_elapsed_second(self):
        today = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        tickets = self.search(
            [('done_date', '<', today), ('is_service_relocation', '=', 'yes'),
             ('state', 'not in', ['draft', 'closed'])])
        self.set_hours_elapsed(tickets, 'second')

    def set_hours_elapsed_third(self):
        today = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        tickets = self.search(
            [('integration_date', '<', today), ('is_service_relocation', '=', 'yes'),
             ('state', 'not in', ['draft', 'closed'])])
        self.set_hours_elapsed(tickets, 'third')



    
    def run_check_service_relocation_escalation_ticket(self):
        dtoday = datetime.today()
        current_hour = dtoday.hour + 1
        is_sunday = False
        if dtoday.weekday() == 6:
            is_sunday = True
        if 8 < current_hour < 18 and not is_sunday:
            self.set_hours_elapsed_first()
            self.escalate_first_service_relocation()
            self.set_hours_elapsed_second()
            self.escalate_second_service_relocation()
            self.set_hours_elapsed_third()
            self.escalate_third_service_relocation()
        return True


    
    def run_check_expected_finished_date_ticket(self):

        is_send_email_expiry_finish = self.env.user.company_id.is_send_email_expiry_finish
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

                # send email back to the QA Team
                partn_ids = []
                user_names = ''
                qa_users = ticket.user_qa_ticket_group_id.sudo().user_ids
                for user in qa_users:
                    if user.is_group_email:
                        user_names += user.name + ", "
                        partn_ids.append(user.partner_id.id)

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
                    msg = _('The Installation Ticket (%s) with subject (%s), having expected finished date as %s, is overdue for closure, by %s hours') % (ticket.ticket_id,ticket.name, exp_date_format,date_diff)
                    self.message_post(
                        msg,
                        subject=msg, partner_ids=partn_ids,
                        subtype_xmlid='mail.mt_comment', force_send=False)

            return True



    
    def write(self, vals):
        res = super(Ticket,self).write(vals)

        assigned_users = vals.get('user_ticket_group_id', False)
        if self.state == 'closed' and self.category_id == self.env.ref('kkon_modifications.kkon_updown_grade'):
            self.partner_id.product_id = self.product_new_id
            self.partner_id.bandwidth = self.bandwidth_new
            self.partner_id.street = self.address_new
            self.partner_id.ip_address = self.adddress_ip_new

        if self.state in ('new','progress') and assigned_users:
            #send email
            partn_ids = []
            user_names = ''
            assign_users = self.user_ticket_group_id.sudo().user_ids
            msg = 'The Ticket (%s) with description (%s), has been re-assigned to %s, by %s' % (
                self.ticket_id, self.name,self.user_ticket_group_id.name, self.env.user.name)
            for user in assign_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

            if partn_ids:
                self.message_post(
                    _(msg),
                    subject='%s' % msg, partner_ids=partn_ids)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        return res

    
    def btn_ticket_progress(self):
        if self.category_id == self.env.ref('kkon_modifications.kkon_maintenance') and self.state == 'new':
            raise UserError(_('Sorry, CTO has to approve the maintenance ticket before it can commence work'))
        return super(Ticket,self).btn_ticket_progress()

    
    def btn_ticket_open(self):
        if not self.category_id or not self.user_ticket_group_id  or not self.user_qa_ticket_group_id  or not self.user_intg_ticket_group_id or not self.expected_finish_date :
            raise UserError(_('Please Select a Category, Assigned User Group and  Expected Finished Date'))

        if self.category_id == self.env.ref('kkon_modifications.kkon_survey'):
            if self.partner_id :
                if not self.location_id or not self.bandwidth:
                    raise UserError(_('Please Set the Location, Bandwidth'))
        # elif self.category_id == self.env.ref('kkon_modifications.kkon_installation') :
        #     if not self.survey_ticket_id or  not self.product_id :
        #         raise UserError(_('Please Select the Site Survey Ticket and set the the Location, Bandwidth, Package for the Customer before the Installation Ticket can be Opened'))
        elif self.category_id not in  (self.env.ref('kkon_modifications.kkon_survey'),self.env.ref('kkon_modifications.kkon_maintenance'),self.env.ref('kkon_modifications.kkon_call_log')) and not self.partner_id:
            raise  UserError(_('Please Set the Customer Name for this ticket to be opened'))
        elif self.category_id == self.env.ref('kkon_modifications.kkon_maintenance'):
            if not self.backend_devices_type and not self.power_type and not self.backhaul_fibre_type and not self.backhaul_microwave_type and not self.access_fibre_type and not self.access_radio_type:
                raise UserError(_('Please select at least a TYPE in the Maintenance TAB'))
            maint_close_group = self.env['user.ticket.group'].search([('is_maint_default', '=', True)], limit=1)
            if not maint_close_group:
                raise UserError(_(
                    'Please contact the Admin to set the Maintenance Closure Group '))
            if not self.base_station_maint_id:
                raise UserError(_('Please Select the Base Station to be maintained in the Maintenance Form below'))
            self.user_maint_ticket_group_id = maint_close_group
        else:
            self.user_maint_ticket_group_id = False

        if self.category_id == self.env.ref('kkon_modifications.kkon_call_log'):
            self.state = 'new_call'
        else:
            self.state = 'new'

        self.open_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.user_id = self.env.user

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
            mail_obj = self.message_post(
                _(msg),
                subject='%s' % msg, partner_ids=partn_ids)

        if self.category_id in [self.env.ref('kkon_modifications.kkon_support'),self.env.ref('kkon_modifications.kkon_updown_grade')]:
            #send carbon copy email to csc group
            csc_users = []
            user_ticket_groups = self.env.user.user_ticket_group_ids
            for user_ticket_group in user_ticket_groups :
                if user_ticket_group.is_csc_kkon_group or user_ticket_group.is_csc_fob_group:
                    csc_users = user_ticket_group.sudo().user_ids

            msg = 'The Ticket (%s) with description (%s), has been Opened by %s' % (
                self.ticket_id, self.name, self.env.user.name)
            partn_csc_ids = []
            for user in csc_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_csc_ids.append(user.partner_id.id)
            if partn_csc_ids and mail_obj:
                mail_obj.email_partner_cc = partn_csc_ids


        #send email to the assigned user
        responsible_user_id = self.responsible_user_id
        if not responsible_user_id :
            raise UserError(_('Please set the assigned user for this ticket to be notified'))
        else:
            msg = 'FYI, you are assigned for the Ticket (%s) with description (%s), which has been Opened by %s' % (
                self.ticket_id, self.name, self.env.user.name)
            self.message_post(
                _(msg),
                subject='%s' % msg, partner_ids=[responsible_user_id.partner_id.id])
            user_names += responsible_user_id.name + ", "

        #Send email to the customer for opening the installation ticket
        partner_id = self.partner_id
        if partner_id and self.category_id == self.env.ref('kkon_modifications.kkon_installation'):
            if self.sudo().ticket_company_id.company_select == 'fob':
                msg = 'Dear %s, <p>This is to acknowledge the receipt of your payment for (Package-%s) Broadband service. </p> An installation ticket with the ID: %s has been opened for your installation. <p> Your Service ID : %s (this will be required for future communication).</p> <p> For further enquiries and assistance, please feel free to contact us through any of the following channels:</p><p><ul class=o_timeline_tracking_value_list><li>Calls: +2349087981900,+2349087981919</li><li>WhatsApp: 08094162890</li><li>Email: salessupport@fob.ng</li><li>MyFOB app,: Download app and click on support.</li></ul></p><p>Please visit our website <a href=https://www.fob.ng/ >https://www.fob.ng</a> for other terms and conditions.</p><p>We appreciate your interest in FiberOne Broadband and we hope you will enjoy our partnership as we provide you a reliable and steady internet connectivity.</p><p> Regards,</p>Customer Service Center</p>' % \
                      (
                          partner_id.name, self.sudo().product_id.name, self.ticket_id, partner_id.ref)
                mail_obj = self.message_post(
                    _(msg),
                    subject='%s Opened Installation Ticket Notification for %s' % (
                    self.sudo().product_id.name, partner_id.name), partner_ids=[partner_id.id])
                user_names += partner_id.name + ", "
                mail_obj.email_from = 'salessupport@fob.ng'
                mail_obj.reply_to = 'salessupport@fob.ng'
            elif self.sudo().ticket_company_id.company_select == 'kkon':
                msg = 'Dear %s, <p>This is to acknowledge the receipt of your payment for (Package-%s) Broadband service. </p> An installation ticket with the ID: %s has been opened for your installation. <p> Your Service ID : %s (this will be required for future communication).</p> <p> For further enquiries and assistance, please feel free to contact us through any of the following channels:</p><p><ul class=o_timeline_tracking_value_list><li>Calls: +234-8180390458, +234-8180390474, +234-8074377163, +234-9087879030</li><li>Email: servicemanagement@kkontech.com</li></ul></p><p>Please visit our website <a href=https://www.kkontech.com/ >https://www.kkontech.com</a> for other terms and conditions.</p><p>We appreciate your interest in KKON Technologies Ltd and we hope you will enjoy our partnership as we provide you a reliable and steady internet connectivity.</p><p> Regards,</p>Customer Service Center</p>' % \
                      (
                          partner_id.name, self.sudo().product_id.name, self.ticket_id, partner_id.ref)
                mail_obj = self.message_post(
                    _(msg),
                    subject='%s Opened Installation Ticket Notification for %s' % (
                    self.sudo().product_id.name, partner_id.name), partner_ids=[partner_id.id])
                user_names += partner_id.name + ", "
                mail_obj.email_from = 'servicemanagement@kkontech.com'
                mail_obj.reply_to = 'servicemanagement@kkontech.com'

        elif partner_id and  self.category_id in [self.env.ref('kkon_modifications.kkon_call_log')]:
            user_tz_obj = pytz.timezone(self.env.context.get('tz') or 'utc')
            localize_tz = pytz.utc.localize
            assigned_date = localize_tz(
                datetime.strptime(self.assigned_date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(user_tz_obj).strftime(
                '%d-%m-%Y')
            msg = 'Dear %s, <p>Thank you for reaching out to us. We acknowledge the receipt of your complaint/enquiry dated - %s with ticket ID - %s .</p> <p> Please note that your satisfaction is very important to us and as such you can be assured of our prompt response at all times.</p> <p> If you require further assistance, please do not hesitate to contact us. </> <p>Regards,</p>' % (
            partner_id.name, assigned_date, self.ticket_id)
            mail_obj = self.message_post(
                _(msg),
                subject='%s Opened Call log Ticket Notification for %s' % (self.sudo().product_id.name, partner_id.name),
                partner_ids=[partner_id.id])
            user_names += partner_id.name + ", "
            if self.sudo().ticket_company_id.company_select == 'fob':
                mail_obj.email_from = 'csc@fob.ng'
                mail_obj.reply_to = 'csc@fob.ng'
            elif self.sudo().ticket_company_id.company_select == 'kkon':
                mail_obj.email_from = 'servicemanagement@kkontech.com'
                mail_obj.reply_to = 'servicemanagement@kkontech.com'

        elif partner_id and  self.category_id in [self.env.ref('kkon_modifications.kkon_support'),self.env.ref('kkon_modifications.kkon_updown_grade')]:
            msg = 'Dear %s (%s), <p>We acknowledge the receipt of your complaints dated - %s with ticket ID - %s </p><p>Thank you for bringing this issue to our attention and we sincerely apologize for any inconvenience this may have caused you.</p><p>Please be assured that your complaint is being taken seriously and as such, you will be contacted shortly on necessary action for resolution.</p><p>Thank you for your patience.</p><p> Regards,</p>Customer Service Center</p>' % \
                  (
                partner_id.name,partner_id.ref, datetime.strptime(self.open_date, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y'), self.ticket_id)
            mail_obj = self.message_post(
                _(msg),
                subject='%s Opened Support Ticket Notification for %s' % (self.sudo().product_id.name,partner_id.name), partner_ids=[partner_id.id])
            user_names += partner_id.name + ", "
            if self.sudo().ticket_company_id.company_select == 'fob':
                mail_obj.email_from = 'csc@fob.ng'
                mail_obj.reply_to = 'csc@fob.ng'
            elif self.sudo().ticket_company_id.company_select == 'kkon':
                mail_obj.email_from = 'servicemanagement@kkontech.com'
                mail_obj.reply_to = 'servicemanagement@kkontech.com'
        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        group_name = 'kin_helpdesk.group_helpdesk_receive_open_ticket_email'
        msg = 'The Ticket (%s) with description (%s), has been Opened by %s' % (
        self.ticket_id, self.name, self.env.user.name)
        #self.send_email(group_name, msg) # Disabled temporarily until the email template for kkon is gotten
        return


    def _compute_duration_maint(self):
        for ticket in self :
            if ticket.start_time_maint and ticket.end_time_maint :
                end_time_maint = datetime.strptime(ticket.end_time_maint , DEFAULT_SERVER_DATETIME_FORMAT)
                start_time_maint = datetime.strptime(ticket.start_time_maint , DEFAULT_SERVER_DATETIME_FORMAT)
                date_diff =  str(end_time_maint - start_time_maint)
                ticket.duration_maint =  date_diff

    def _compute_close_duration(self):
        for ticket in self :
            if ticket.open_date and ticket.state not in ('closed','cancel','draft') :
                open_date = datetime.strptime(ticket.open_date , DEFAULT_SERVER_DATETIME_FORMAT)
                now_date = datetime.strptime(datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),DEFAULT_SERVER_DATETIME_FORMAT)
                date_diff =  str(now_date - open_date)
                ticket.duration_close =  date_diff



    
    def action_view_crm(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('CRM'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'crm.lead',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.crm_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('crm_id')
    def _compute_crm_count(self):
        for rec in self:
            rec.crm_count = len(rec.crm_id)

    
    def action_view_order(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.order_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('order_id')
    def _compute_order_count(self):
        for rec in self:
            rec.order_count = len(rec.order_id)


    
    def action_view_invoice(self):
        invoice_id = self.mapped('invoice_id')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
             'target': 'new',
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


    # @api.onchange('partner_id')
    # def onchange_partner(self):
    #     self.location_id = self.partner_id.location_id
    #     self.base_station_id = self.partner_id.base_station_id



    def create_customer_invoice(self,order):

        if not self.installation_date :
            raise UserError(_('Please Set the Installation Date'))

        if not self.config_status :
            raise UserError(_('Please Set the Configuration Status'))

        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}

        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))

        sale_order = order
        invoice_vals = {
            'name': sale_order.name or '',
            'date_invoice' : self.installation_date,
            'origin': sale_order.name,
            'type': 'out_invoice',
            'reference': sale_order.client_order_ref or self.name,
            'account_id': sale_order.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': sale_order.partner_invoice_id.id,
            'journal_id': journal_id,
            'currency_id': sale_order.pricelist_id.currency_id.id,
            'comment': sale_order.note,
            'payment_term_id': sale_order.payment_term_id.id,
            #'fiscal_position_id': sale_order.fiscal_position_id.id or sale_order.partner_invoice_id.property_account_position_id.id,  # this causes account not be found on the product category below. Please avoid it
            'company_id': sale_order.company_id.id,
            'user_id': sale_order.user_id and sale_order.user_id.id,
            'team_id': sale_order.team_id.id,
            'incoterms_id': sale_order.incoterm.id or False,
            'sale_id' :sale_order.id,
            'is_installation_invoice' : True,
            'installation_ticket_id' : self.id,
        }
        invoice = inv_obj.create(invoice_vals)

        lines = []
        for sale_order_line_id in order.order_line:
            if not float_is_zero(sale_order_line_id.product_uom_qty, precision_digits=precision):
                account = sale_order_line_id.product_id.property_account_income_id or sale_order_line_id.product_id.categ_id.property_account_income_categ_id
                if not account:
                    raise UserError(
                        _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % (
                            sale_order_line_id.product_id.name, sale_order_line_id.product_id.id,
                            sale_order_line_id.product_id.categ_id.name))


                default_analytic_account = self.env['account.analytic.default'].account_get(
                    sale_order_line_id.product_id.id, sale_order_line_id.order_id.partner_id.id,
                    sale_order_line_id.order_id.user_id.id, date.today())


                inv_line = {
                        'name': sale_order_line_id.name,
                        'sequence': sale_order_line_id.sequence,
                        'origin': sale_order_line_id.order_id.name,
                        'account_id': account.id,
                        'price_unit': sale_order_line_id.price_unit,
                        'quantity': sale_order_line_id.product_uom_qty,
                        'discount': sale_order_line_id.discount,
                        'uom_id': sale_order_line_id.product_uom.id,
                        'product_id': sale_order_line_id.product_id.id,
                    # This will no longer causes the validated invoice to create COG entries from Goods Dispatched, because a service product is used instead of a stock product
                        'invoice_line_tax_ids': [(6, 0, sale_order_line_id.tax_id.ids)],
                        'account_analytic_id': sale_order_line_id.order_id.project_id.id or default_analytic_account and default_analytic_account.analytic_id.id,
                        'invoice_id': invoice.id,
                        'sale_line_ids': [(6, 0, [sale_order_line_id.id])]
                    # Never remove this sale_line_ids. This determines the cost of goods sold using the FIFO and not from the product page
                }
                self.env['account.invoice.line'].create(inv_line)


        if not invoice.invoice_line_ids:
            raise UserError(_('There is no invoiceable line.'))
            # If invoice is negative, do a refund invoice instead
        if invoice.amount_untaxed < 0:
            invoice.type = 'out_refund'
            for line in invoice.invoice_line_ids:
                line.quantity = -line.quantity
        # Use additional field helper function (for account extensions)
        for line in invoice.invoice_line_ids:
            line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
        invoice.compute_taxes()
        self.invoice_id = invoice


        #Send Email to accountants
        user_ids = []
        group_obj = self.env.ref('account.group_account_invoice')
        for user in group_obj.sudo().users:
            if user.is_group_email:
                user_ids.append(user.partner_id.id)

        if user_ids:
            invoice.message_post(_(
                    'A New Installation Invoice has been created from  %s for the Ticket with ID %s.') % (
                                  self.env.user.name, self.name),
                              subject='A New Installation Invoice has been created ',partner_ids=[user_ids], subtype_xmlid='mail.mt_comment', force_send=False)

        return invoice


    @api.onchange('partner_id')
    def onchange_partner(self):
        self.product_curr_id = self.partner_id.product_id
        self.bandwidth_current = self.partner_id.bandwidth
        self.address_old = self.partner_id.street
        self.address_ip_current = self.partner_id.ip_address


    @api.onchange('location_id')
    def onchange_location(self):
        self.base_station_id = ''

    
    def btn_ticket_reset(self):
        for rec in self:
            rec.invoice_id.unlink()
        return super(Ticket, self).btn_ticket_reset()

    
    def btn_ticket_cancel(self):
        for rec in self:
            rec.invoice_id.unlink()
        return super(Ticket, self).btn_ticket_cancel()

    
    def unlink(self):
        for rec in self:
            rec.invoice_id.unlink()
        return super(Ticket,self).unlink()

    
    def btn_ticket_done(self):

        if self.category_id == self.env.ref('kkon_modifications.kkon_installation') and self.order_id:
            if not self.cpe:
                raise UserError(_('Please set the CPE Model on the Customer Details Form Tab'))
            if  not self.olt_id or not self.gpon_level or not self.power_level_id or not self.idu_serial_no or not self.wifi_ssid or not self.splitter_box_code or not self.region_id or not self.installation_fse_id or not self.installation_approver_id or not self.wireless_technology or not self.rssi_id or not self.radio_ip_addr or not self.indoor_ip_address or not self.ap_ip_address or not self.radio_model or not self.comment_activation:
                raise UserError(_('Please Set the Fields in the Activation Form Tab Below'))

        if self.category_id == self.env.ref('kkon_modifications.kkon_support'):
            if not self.root_cause or  not self.resolution :
                raise UserError(_('Please Set the Root Cause and Resolution in the Other Information Tab'))


        # if self.category_id == self.env.ref('kkon_modifications.kkon_survey'):
        #     if not self.site_survey_form:
        #         raise UserError(_('Please attach the Site Survey Form'))

        partn_ids = []
        user_names = ''
        if self.category_id == self.env.ref('kkon_modifications.kkon_maintenance'):
            # if not self.maint_form :
            #     raise UserError(_('Please attach the Maintenance Schedule form in the Maintenance Form Tab'))
            # if  not self.base_station_maint_id or not self.rfs_in_charge or not self.rf_contact_maint or not self.purpose_maint or not self.date_maint or not self.start_time_maint or not self.end_time_maint or not self.pop  or not self.service_impact or not self.services or not self.pop_affected :
            #     raise UserError(_('Please fill in the fields in the Maintenance Form Tab'))
            if not self.backend_devices_type and not self.power_type and not self.backhaul_fibre_type and not self.backhaul_microwave_type and not self.access_fibre_type and not self.access_radio_type:
                raise UserError(_('Please select at least a TYPE in the Maintenance TAB'))
            init_users = self.initiator_ticket_group_id.sudo().user_ids
            for user in init_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

            # To service Mgt. people
            group_serv_obj = self.env.ref('kkon_modifications.group_kkon_ticket_service_mgt')
            for suser in group_serv_obj.sudo().users:
                user_names += suser.name + ", "
                partn_ids.append(suser.partner_id.id)

        #send email to the QA Team
        qa_users  = self.user_qa_ticket_group_id.sudo().user_ids
        msg = 'The Ticket (%s) with description (%s), has been Done by %s' % (
        self.ticket_id, self.name, self.env.user.name)
        for user in qa_users:
            if user.is_group_email:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_post(
                _(msg),
                subject='%s' % msg, partner_ids=partn_ids)

        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
        self.done_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return super(Ticket,self).btn_ticket_done()

    
    def btn_ticket_close(self):

        if self.category_id == self.env.ref('kkon_modifications.kkon_installation') and self.order_id :
            self.order_id.is_installation_ticket_close = True

            #set partner parameters
            self.partner_id.config_status = self.config_status
            self.partner_id.installation_date = self.installation_date

            #create invoice
            if self.order_id :
                if self.invoice_id :
                    raise UserError('Sorry, this ticket has been previously closed and invoice created. Please refresh your browser')

                 #For now disable invoice creation for Kkontech
                if self.sudo().ticket_company_id.company_select == 'fob':
                    invoice = self.create_customer_invoice(self.order_id)
                    invoice.compute_taxes()
                    invoice.signal_workflow('invoice_open')
                elif self.sudo().ticket_company_id.company_select == 'kkon':
                    if self.is_upcountry:
                        invoice = self.create_customer_invoice(self.order_id)
                        invoice.compute_taxes()
                        invoice.signal_workflow('invoice_open')
                        invoice.is_upcountry = True


            # send email
            user_ids = []
            group_obj = self.env.ref('kkon_modifications.group_kkon_ticket_installation_close_notify')
            user_names = ''
            for user in group_obj.users:
                user_names += user.name + ", "
                user_ids.append(user.partner_id.id)

            #To service Mgt. people
            group_serv_obj = self.env.ref('kkon_modifications.group_kkon_ticket_service_mgt')
            for suser in group_serv_obj.sudo().users:
                user_names += suser.name + ", "
                user_ids.append(suser.partner_id.id)

            #To sales person that won the opportunity
            if self.order_id :
                sale_person = self.order_id.sudo().user_id
                if sale_person:
                    user_names += sale_person.name + ", "
                    user_ids.append(sale_person.partner_id.id)

            if user_ids:
                self.message_post(
                    _(
                        'The Installation Ticket %s has been closed for the order id - %s, from %s') % (
                        self.name,self.order_id.name, self.env.user.name),
                    subject='An Installation Ticket has been closed',partner_ids=[user_ids], subtype_xmlid='mail.mt_comment', force_send=False)



            # Send email to the customer for closing the installation ticket
            partner_id = self.partner_id
            if partner_id:
                partner_id.send_welcome_customer_email()
                msg = 'Dear %s, <p>This is to notify you that we have completed and closed the process of installing your package - %s . An installation ticket with the ID: %s has been completed and closed.  </p> <p>Thanks for your patronage. We hope you enjoy the service</p><p>Regards</p>' % (
                    self.partner_id.name, self.sudo().product_id.name, self.ticket_id)
                mail_obj = self.message_post(
                    _(msg),
                    subject='%s Completed and Closed Installation Ticket Notification for %s' % (self.sudo().product_id.name, partner_id.name), partner_ids=[partner_id.id])
                user_names += partner_id.name + ", "
                if self.sudo().ticket_company_id.company_select == 'fob':
                    mail_obj.email_from = 'salessupport@fob.ng'
                    mail_obj.reply_to = 'salessupport@fob.ng'
                elif self.sudo().ticket_company_id.company_select == 'kkon':
                    mail_obj.email_from = 'servicemanagement@kkontech.com'
                    mail_obj.reply_to = 'servicemanagement@kkontech.com'

            self.env.user.notify_info('%s Will Be Notified by Email for Installation Ticket Closure' % (user_names))

        elif self.category_id == self.env.ref('kkon_modifications.kkon_survey') and self.crm_id:
            self.crm_id.is_survey_ticket_close = True
            # send email
            user_ids = []
            group_obj = self.env.ref('kkon_modifications.group_kkon_ticket_survey_close_notify')
            user_names = ''
            for user in group_obj.sudo().users:
                user_names += user.name + ", "
                user_ids.append(user.partner_id.id)
            self.message_post(
                _(
                    'The Survey Ticket %s has been closed for the order id - %s, from %s') % (
                    self.name, self.order_id.name,self.env.user.name),
                subject='The Survey Ticket has been closed',partner_ids=user_ids, subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email for Survey Ticket Closure' % (user_names))

        elif self.category_id == self.env.ref('kkon_modifications.kkon_updown_grade'):
            # send email
            user_ids = []
            group_obj = self.env.ref('kkon_modifications.group_kkon_ticket_updown_close_notify')
            user_names = ''
            for user in group_obj.sudo().users:
                user_names += user.name + ", "
                user_ids.append(user.partner_id.id)
            self.message_post(
                _(
                    'The Change Request Ticket %s has been closed by %s') % (
                    self.name,self.env.user.name),
                subject='The Change Request Ticket has been closed',partner_ids=user_ids, subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email for Change Request Ticket Closure' % (user_names))

        elif self.category_id == self.env.ref('kkon_modifications.kkon_call_log'):
            user_names = ''
            # Send email to the customer for closing the call log ticket
            partner_id = self.partner_id
            if partner_id:
                msg = 'Dear %s, <p>This is to notify you that we have completed and closed the issue with id - %s . A call log ticket with the ID: %s has been completed and closed.  </p> <p>Thanks for your patronage. We hope you enjoy the service</p><p>Regards</p>' % (
                    self.partner_id.name, self.ticket_id, self.ticket_id)
                mail_obj = self.message_post(
                    _(msg),
                    subject='Completed and Closed call log Ticket Notification for %s' % (
                     partner_id.name), partner_ids=[partner_id.id])
                user_names += partner_id.name + ", "
                if self.sudo().ticket_company_id.company_select == 'fob':
                    mail_obj.email_from = 'csc@fob.ng'
                    mail_obj.reply_to = 'csc@fob.ng'
                elif self.sudo().ticket_company_id.company_select == 'kkon':
                    mail_obj.email_from = 'servicemanagement@kkontech.com'
                    mail_obj.reply_to = 'servicemanagement@kkontech.com'
        return super(Ticket,self).btn_ticket_close()

    
    def btn_ticket_close_call(self):

        if self.category_id == self.env.ref('kkon_modifications.kkon_call_log'):

            user_names = ''
            # Send email to the customer for closing the call log ticket
            partner_id = self.partner_id
            if partner_id:
                user_tz_obj = pytz.timezone(self.env.context.get('tz') or 'utc')
                localize_tz = pytz.utc.localize
                assigned_date = localize_tz(datetime.strptime(self.assigned_date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(user_tz_obj).strftime('%d-%m-%Y')
                msg = 'Dear %s, <p>In response to your internet complaint received on - %s with ticket ID - %s. Our support representative reported that your network issue has been resolved. You a valued customer and your satisfaction is our top priority at every point of interaction, we would like to hear from you if this issue was resolved to your satisfaction. <p><p>Please do not hesitate to contact us if you require further assistance.</p><p>Regards,</p><p>Customer Service Center</p>' % (self.partner_id.name, assigned_date, self.ticket_id)
                mail_obj = self.message_post(
                    _(msg),
                    subject='Closed call log Ticket Notification for %s' % (
                     partner_id.name), partner_ids=[partner_id.id])
                user_names += partner_id.name + ", "
                if self.sudo().ticket_company_id.company_select == 'fob':
                    mail_obj.email_from = 'csc@fob.ng'
                    mail_obj.reply_to = 'csc@fob.ng'
                elif self.sudo().ticket_company_id.company_select == 'kkon':
                    mail_obj.email_from = 'servicemanagement@kkontech.com'
                    mail_obj.reply_to = 'servicemanagement@kkontech.com'


            # send email
            user_ids = []
            group_obj = self.env.ref('kkon_modifications.group_kkon_ticket_call_close_notify')
            user_names = ''
            for user in group_obj.users:
                user_names += user.name + ", "
                user_ids.append(user.partner_id.id)

            if user_ids:
                self.message_post(
                    _(
                        'The Call Log Ticket %s has been closed by %s') % (
                        self.name, self.env.user.name),
                    subject='A Call Log Ticket has been closed',partner_ids=[user_ids], subtype_xmlid='mail.mt_comment', force_send=False)

            self.env.user.notify_info('%s Will Be Notified by Email for Call log Ticket Closure' % (user_names))

        return super(Ticket,self).btn_ticket_close()


    #QA (NOC) approves ticket
    
    def btn_ticket_qa(self):
        self.state = 'qa'
        if self.category_id in (self.env.ref('kkon_modifications.kkon_installation'),self.env.ref('kkon_modifications.kkon_updown_grade')) :
            # if not self.qa_form:
            #     raise UserError(_('Please Attach the Quality Assurance Form'))

            # send email to the Integration Team (Backend)
            partn_ids = []
            user_names = ''
            intg_users = self.user_intg_ticket_group_id.sudo().user_ids
            msg = 'The Ticket (%s) with description (%s), has been approved by %s from the QA team' % (
                self.ticket_id, self.name, self.env.user.name)
            for user in intg_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

            # init_users = self.initiator_ticket_group_id.sudo().user_ids
            # for user in init_users:
            #     if user.is_group_email:
            #         user_names += user.name + ", "
            #         partn_ids.append(user.partner_id.id)
            #
            # qa_users = self.user_qa_ticket_group_id.sudo().user_ids
            # for user in qa_users:
            #     if user.is_group_email:
            #         user_names += user.name + ", "
            #         partn_ids.append(user.partner_id.id)
            #
            # assign_users = self.user_ticket_group_id.sudo().user_ids
            # for user in assign_users:
            #     if user.is_group_email:
            #         user_names += user.name + ", "
            #         partn_ids.append(user.partner_id.id)

            if partn_ids:
                self.message_post(
                    _(msg),
                    subject='%s' % msg, partner_ids=partn_ids)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        if self.category_id in [self.env.ref('kkon_modifications.kkon_support')] or self.category_id == self.env.ref('kkon_modifications.kkon_maintenance'):
            self.state = 'integration'
            #send email to the csc support team
            partn_ids = []
            user_names = ''
            users = self.initiator_ticket_group_id.sudo().user_ids
            msg = 'The Ticket (%s) with description (%s), has been done by %s' % (
                self.ticket_id, self.name, self.env.user.name)
            for user in users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

            if partn_ids:
                mail_obj = self.message_post(
                    _(msg),
                    subject='%s' % msg, partner_ids=partn_ids)


            #send email to the customer
            partner_id = self.partner_id
            msg = 'Dear %s (%s), <p>In response to your complaint received on %s</p><p>Our support representative reported that your network issue was resolved on %s</p><p>We would like to hear from you if this issue was resolved to your satisfaction. Please note that if we do not hear from you after 48hours, we will assume your network issue has been resolved and the ticket will be closed.</p><p>You a valued customer and our desire is to ensure that you receive quality service at every point of interaction with us.</p><p>Please do not hesitate to contact us if you require further assistance.</p><p> Regards,</p>Customer Service Center</p>' % \
                  (
                partner_id.name, partner_id.ref, self.sudo().product_id.name,  datetime.strptime(self.done_ticket_date, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S') )
            mail_obj = self.message_post(
                _(msg),
                subject='%s (%s) Resolved Support Ticket Notification' % (partner_id.name,partner_id.ref), partner_ids=[partner_id.id])
            user_names += partner_id.name + ", "

        if self.category_id == self.env.ref('kkon_modifications.kkon_support'):
            # change the email_from and reply_to field to the csc group
            if self.sudo().ticket_company_id.company_select == 'fob':
                mail_obj.email_from = 'csc@fob.ng'
                mail_obj.reply_to = 'csc@fob.ng'
            elif self.sudo().ticket_company_id.company_select == 'kkon':
                mail_obj.email_from = 'servicemanagement@kkontech.com'
                mail_obj.reply_to = 'servicemanagement@kkontech.com'

        if self.category_id == self.env.ref('kkon_modifications.kkon_survey'):
            raise UserError(_("Sorry, Surveys Don't Need Quality Assurance"))

        group_name = 'kkon_modifications.group_helpdesk_receive_qa_ticket_email'
        msg = 'The Ticket (%s) with description (%s), has been approved by %s from the QA team' % (
        self.ticket_id, self.name, self.env.user.name)
        self.send_email(group_name, msg)


    #CTO approves maintenance ticket
    
    def btn_ticket_maint_approve(self):
        if self.category_id != self.env.ref('kkon_modifications.kkon_maintenance') :
            raise UserError(_('Sorry, you may rather Click the Done button. This is not a maintenance ticket'))

        self.state = 'maint_approve'
        if self.category_id == self.env.ref('kkon_modifications.kkon_maintenance') :

            # send email to the Integration Team (Backend)
            partn_ids = []
            user_names = ''
            intg_users = self.user_intg_ticket_group_id.sudo().user_ids
            msg = 'The Maintenance Ticket (%s) with description (%s), has been approved by %s from the CTO' % (
                self.ticket_id, self.name, self.env.user.name)
            for user in intg_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

            init_users = self.initiator_ticket_group_id.sudo().user_ids
            for user in init_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

            #To service Mgt. people
            group_serv_obj = self.env.ref('kkon_modifications.group_kkon_ticket_service_mgt')
            for suser in group_serv_obj.sudo().users:
                user_names += suser.name + ", "
                partn_ids.append(suser.partner_id.id)

            # qa_users = self.user_qa_ticket_group_id.sudo().user_ids
            # for user in qa_users:
            #     if user.is_group_email:
            #         user_names += user.name + ", "
            #         partn_ids.append(user.partner_id.id)
            #
            # assign_users = self.user_ticket_group_id.sudo().user_ids
            # for user in assign_users:
            #     if user.is_group_email:
            #         user_names += user.name + ", "
            #         partn_ids.append(user.partner_id.id)

            if partn_ids:
                self.message_post(
                    _(msg),
                    subject='%s' % msg, partner_ids=partn_ids)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        group_name = 'kkon_modifications.group_helpdesk_receive_maint_ticket_email'
        msg = 'The Maintenance Ticket (%s) with description (%s), has been approved by %s from the CTO' % (
        self.ticket_id, self.name, self.env.user.name)
        self.send_email(group_name, msg)


    
    def action_ticket_qa_reject(self,msg):
        self.state = 'progress'
        self.qa_disapprove_by = self.env.user
        self.qa_disapprove_date = datetime.today()
        self.qa_disapprove_msg = msg

        if self.category_id == self.env.ref('kkon_modifications.kkon_survey'):
            raise UserError(_("Sorry, Surveys Don't Need Quality Assurance"))

        if self.category_id == self.env.ref('kkon_modifications.kkon_installation'):
            if not self.rejection_evidence:
                raise UserError(_('Please Attach the Rejection Evidence'))

            # send email back to the QA Team
            partn_ids = []
            user_names = ''
            qa_users = self.user_qa_ticket_group_id.sudo().user_ids
            mesg = 'The Ticket (%s) with description (%s), has been Dis-approved by %s from the QA team  with reason: (%s)' % (
                    self.ticket_id, self.name, self.env.user.name,msg)
            for user in qa_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

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
                self.message_post(
                        _(mesg),
                        subject='%s' % mesg, partner_ids=partn_ids)

            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        group_name = 'kkon_modifications.group_helpdesk_receive_qa_ticket_email'
        mesg = 'The Ticket (%s) with description (%s), has been Dis-approved by %s from the QA team with reason: (%s)' % (
            self.ticket_id, self.name, self.env.user.name,msg)
        self.send_email(group_name, mesg)

    
    def action_ticket_opener_reject(self, msg):
        self.state = 'progress'
        self.opener_disapprove_by = self.env.user
        self.opener_disapprove_date = datetime.today()
        self.opener_disapprove_msg = msg

        if self.category_id == self.env.ref('kkon_modifications.kkon_survey'):
            raise UserError(_("Sorry, This action is Not Necessary Surveys "))
        else:
            # send email back to the QA Team
            partn_ids = []
            user_names = ''
            opener_users = self.user_qa_ticket_group_id.sudo().user_ids
            mesg = 'The Ticket (%s) with description (%s), has been Rejected by %s with reason: (%s)' % (
                self.ticket_id, self.name, self.env.user.name, msg)
            for user in opener_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

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
                self.message_post(
                    _(mesg),
                    subject='%s' % mesg, partner_ids=partn_ids)

            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        group_name = 'kkon_modifications.group_helpdesk_receive_qa_ticket_email'
        mesg = 'The Ticket (%s) with description (%s), has been Dis-approved by %s from the QA team with reason: (%s)' % (
            self.ticket_id, self.name, self.env.user.name, msg)
        self.send_email(group_name, mesg)


    
    def action_ticket_maint_reject(self,msg):

        if self.category_id != self.env.ref('kkon_modifications.kkon_maintenance') :
            raise UserError(_('Sorry, you may rather Click the Done button. This is not a maintenance ticket'))

        self.state = 'draft'



        self.maint_disapprove_by = self.env.user
        self.maint_disapprove_date = datetime.today()
        self.maint_disapprove_msg = msg

        if self.category_id == self.env.ref('kkon_modifications.kkon_maintenance'):
            # send email back to the QA Team
            partn_ids = []
            user_names = ''
            qa_users = self.user_qa_ticket_group_id.sudo().user_ids
            mesg = 'The Maintenance Ticket (%s) with description (%s), has been Declined by %s from the CTO  with reason: (%s)' % (
                self.ticket_id, self.name, self.env.user.name, msg)
            for user in qa_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)

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
                self.message_post(
                    _(mesg),
                    subject='%s' % mesg, partner_ids=partn_ids)

            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        group_name = 'kkon_modifications.group_helpdesk_receive_maint_ticket_email'
        mesg = 'The Maintenance Ticket (%s) with description (%s), has been Declined by %s from the CTO with reason: (%s)' % (
            self.ticket_id, self.name, self.env.user.name,msg)
        self.send_email(group_name, mesg)

    
    def btn_ticket_integration(self):
        self.state = 'integration'

        if self.category_id == self.env.ref('kkon_modifications.kkon_installation'):
            if not self.ip_address or not self.radio_ip_address or  not self.base_station_ip_address or  not self.subnet or not self.gateway or not self.indoor_wan or not self.comment:
                raise UserError(_('Please Set the Customer IP Address,  Radio IP Address,  Base Station IP Address, Subnet,  Gateway, In Door WAN IP Address and Comment fields'))

        group_name = 'kkon_modifications.group_helpdesk_receive_integration_ticket_email'
        msg = 'The Ticket (%s) with description (%s), has been approved by %s, from the Integration team' % (
            self.ticket_id, self.name, self.env.user.name)
        self.send_email(group_name, msg)

        #send email to QA team (NOC)
        partn_ids = []
        user_names = ''
        qa_users = self.user_qa_ticket_group_id.sudo().user_ids
        msg = 'The Ticket (%s) with description (%s), has been approved by %s from the Integration team' % (
            self.ticket_id, self.name, self.env.user.name)
        for user in qa_users:
            if user.is_group_email:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

        #ticket opener users
        ope_users = self.initiator_ticket_group_id.sudo().user_ids
        for user in ope_users:
            if user.is_group_email:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

        if not partn_ids : #this can happen for FOB installation ticket opener group without the group email
            for user in ope_users:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_post(
                _(msg),
                subject='%s' % msg, partner_ids=partn_ids)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
        self.integration_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    #Integration rejection
    
    def action_ticket_reject(self,msg):
        self.state = 'done'
        self.integration_reject_by = self.env.user
        self.integration_rejection_date = datetime.today()
        self.integration_reject_msg = msg

        group_name = 'kkon_modifications.group_helpdesk_receive_integration_ticket_email'
        mesg = 'The Ticket (%s) with description (%s), has been Dis-approved by %s, from the Integration team, with reason: (%s)' % (
            self.ticket_id, self.name, self.env.user.name,msg)
        self.send_email(group_name, mesg)



    def get_default_eng_group(self):
        company = self.company_id
        if not  company:
            company = self.env.user.company_id
        res = self.env['user.ticket.group'].search([('is_eng_default','=',True),('company_id','=',company.id)],limit=1)
        return res

    def get_default_qa_group(self):
        company = self.company_id
        if not  company:
            company = self.env.user.company_id
        res = self.env['user.ticket.group'].search([('is_qa_default','=',True)],limit=1)
        return res

    def get_default_intg_group(self):
        company = self.company_id
        if not  company:
            company = self.env.user.company_id
        res = self.env['user.ticket.group'].search([('is_intg_default','=',True)],limit=1)
        return res

    def get_initiator_group(self):
        company = self.company_id
        if not company:
            company = self.env.user.company_id
        res = self.env['user.ticket.group'].search([('user_ids', '=', self.env.user.id)],limit=1)
        return res

    #remove
    #
    # the store=True for the related fields, because it prevents the helpdesk user from saving a ticket with partner information if there are other tickets attached to the partner, and the user is not in the group for all the previous tickets attached to the partner. so the helpdesk user rule prevents it from saving the form for the related fields with store parameter, since it will want to update the partner which inturns update all other previous tickets having the store=True paramter ( I have tested the fact  the system updates other previous tickets indirectly, whne given the  Helpdesk general manager rights which have access to all tickets)
    cust_name = fields.Char(related='partner_id.name', string='Name', readonly=True)
    street = fields.Char(related='partner_id.street', string='Address', readonly=True)
    website = fields.Char(related='partner_id.website', string='Website', readonly=True)
    company_id = fields.Many2one(related='partner_id.company_id', string='Company', readonly=True)
    ref = fields.Char(related='partner_id.ref', string='Client ID', readonly=True)
    location_id = fields.Many2one(related='partner_id.location_id', string='Location')
    region_cust_id = fields.Many2one(related='partner_id.region_id', string='Region')
    area_customer_id = fields.Many2one(related='partner_id.area_id', string='Area',store=True)
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
    installation_date = fields.Date(string='Installation Date')
    config_status = fields.Char(string='Configuration Status')
    function = fields.Char(related='partner_id.function', string='Job Position', readonly=True)
    phone = fields.Char(related='partner_id.phone', string='Phone', readonly=True)
    mobile = fields.Char(related='partner_id.mobile', string='Mobile', readonly=True)
    fax = fields.Char(related='partner_id.fax', string='Fax', readonly=True)
    email = fields.Char(related='partner_id.email', string='Email', readonly=True)
    # title = fields.Many2one(related='partner_id.title', string='Title', readonly=True)
    # lang = fields.Selection(related='partner_id.lang', string='Language', readonly=True)
    # category_ids = fields.Many2many(related='partner_id.category_id', string='Tags', readonly=True)
    client_type_id = fields.Many2one(related='partner_id.client_type_id')
    order_id = fields.Many2one('sale.order', string='Order')
    order_count = fields.Integer(compute="_compute_order_count", string='# of CRMs', copy=False, default=0)
    crm_id = fields.Many2one('crm.lead', string='CRM')
    crm_count = fields.Integer(compute="_compute_crm_count", string='# of CRMs', copy=False, default=0)
    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    invoice_count = fields.Integer(compute="_compute_invoice_count", string='# of Invoices', copy=False, default=0)

    title = fields.Many2one(related='partner_id.title',string="Title", readonly=True)
    first_name  = fields.Char(related='partner_id.first_name', string="First Name", readonly=True)
    last_name  = fields.Char(related='partner_id.last_name', string="Last Name", readonly=True)
    gender = fields.Selection(related='partner_id.gender',  string='Gender', readonly=True)    
    estate_id = fields.Many2one(related='partner_id.estate_id',string='Estate', readonly=True)
    city_cust = fields.Char(related='partner_id.city_cust',string='City', readonly=True)  
    dob = fields.Date(related='partner_id.dob',string="DOB", readonly=True)
    state_ng = fields.Selection(related='partner_id.state_ng',string="State", readonly=True)

    expiration = fields.Date(related='partner_id.expiration',string="Expiration")
    reg_date = fields.Date(related='partner_id.reg_date', string="REG Date")
    last_logoff = fields.Date(related='partner_id.last_logoff', string="Last Logoff")
    gpon = fields.Char(related='partner_id.gpon', string="GPON")
    interface = fields.Char(related='partner_id.interface', string="Interface")
    serial_no = fields.Char(related='partner_id.serial_no', string="Serial No")

    survey_ticket_id = fields.Many2one('kin.ticket',string='Site Survey Ticket')
    #product_ids = fields.Many2many(related='partner_id.product_ids',string='Package(s)')
    product_id = fields.Many2one(related='partner_id.product_id',string='Package')
    installation_form = fields.Binary(string='Installation Picture', attachment=True)
    qa_form = fields.Binary(string='Quality Assurance Form')
    rejection_evidence = fields.Binary(string='Rejection Evidence')
    #maint_form = fields.Binary(string='Maintenance Schedule Form')
    access_confirmation = fields.Char(string="Confirmation of access to the location")
    installation_constraint = fields.Text(string="Constraints that could delay the installation")
    survey_attachment = fields.Binary(string="Survey Attachment Picture/FIle")

    root_cause = fields.Text(string='Root Cause')
    resolution = fields.Text(string='Resolution')
    call_type_support = fields.Selection([('inbound_support', 'Inbound Support'), ('inbound_enquiry', 'Inbound Enquiry'),
                                  ('outbound_retention', 'Outbound Retention')], string='Support Call Type')
    source_support = fields.Selection(
        [('call', 'Call'), ('email', 'Email'),
         ('chat', 'Chat'),('web', 'Web'),('eservice', 'Eservice'),('epclekki', 'EPC Lekki'),('twitter', 'Twitter'),('googlereview', 'Google Review'),('whatsapp', 'Whatsapp')], string='Source')
    complaint_type_support_id = fields.Many2one('kkon.complaint.type', string='Complaint Type')
    done_ticket_date = fields.Datetime(string='Resolved Ticket Date')
    qa_disapprove_msg = fields.Text(string='QA. Dispprove Reason')
    qa_disapprove_by = fields.Many2one('res.users',string='Dis-approved By')
    qa_disapprove_date = fields.Datetime(string='Dis-approved Date and Time')
    maint_disapprove_msg = fields.Text(string='Declined Reason')
    maint_disapprove_by = fields.Many2one('res.users', string='Declined By')
    maint_disapprove_date = fields.Datetime(string='Declined Date and Time')

    opener_disapprove_msg = fields.Text(string='Ticket Opener Rejection Reason')
    opener_disapprove_by = fields.Many2one('res.users', string='Rejected By')
    opener_disapprove_date = fields.Datetime(string='Rejection Date and Time')

    integration_reject_msg = fields.Text(string='Integration Rejection Reason')
    integration_reject_by = fields.Many2one('res.users',string='Rejected By')
    integration_rejection_date = fields.Datetime(string='Rejection Date and Time')

    user_qa_ticket_group_id = fields.Many2one('user.ticket.group',default=get_default_qa_group, string='QA User Group',ondelete='restrict')
    # qa_ids = fields.Many2many('res.users', 'qa_users_ticket_rel', 'qa_user_id', 'ticket_id',  string='QA Team', related='user_qa_ticket_group_id.user_ids'
    #                                 )
    user_intg_ticket_group_id = fields.Many2one('user.ticket.group',default=get_default_intg_group, string='Integration User Group',ondelete='restrict')
    # intg_ids = fields.Many2many('res.users', 'intg_users_ticket_rel', 'intg_user_id', 'ticket_id', string='Integration Team', related='user_intg_ticket_group_id.user_ids'
    #                           )
    initiator_ticket_group_id = fields.Many2one('user.ticket.group',default=get_initiator_group,string='Ticket Opener Group')
    user_ticket_group_id = fields.Many2one('user.ticket.group', default=get_default_eng_group, string='Assigned User Group')
    user_maint_ticket_group_id = fields.Many2one('user.ticket.group',string='Maintenance Ticket Close Group' )


    state = fields.Selection(
        [('draft', 'Draft'), ('new', 'Open'),('new_call', 'Open Call Log'), ('maint_approve', 'Maint. Approved'), ('progress', 'Work In Progress'),('done', 'Completed'), ('qa','Quality Assured'), ('integration','Finalized'),('closed', 'Closed'),('cancel', 'Cancelled')],
        default='draft', tracking=True)

    responsible_user_id = fields.Many2one('res.users', string='Assigned User')
    description = fields.Text(string='Incident Details')

    #SUrvey Form fields
    site_survey_form = fields.Binary(string='Site Survey Form', attachment=True)
    srf_form = fields.Binary(string='SRF Form', attachment=True)
    # survey_details = fields.Text(string='Survey Details')
    dist_fpop = fields.Char(string='Distance to FPOP')
    fpop_box_jb = fields.Char(string='FPOP Box / JB')
    equipment_required = fields.Char(string='Equipment Required')
    comment_survey = fields.Text(string='Comment')


    #Maintenance form fields
    base_station_maint_id = fields.Many2one('base.station', string='Base Station')
    rfs_in_charge = fields.Many2one('res.users',string='RFS IN CHARGE')
    rf_contact_maint = fields.Char(string='RF Contact')
    purpose_maint = fields.Char(string='PURPOSE')
    date_maint = fields.Date(string='MAINTENANCE DATE')
    start_time_maint = fields.Datetime(string='START TIME')
    end_time_maint = fields.Datetime(string='END TIME')
    duration_maint = fields.Char(string='DURATION',compute=_compute_duration_maint)
    pop = fields.Char(string='POP')
    backend_devices_type = fields.Boolean(string='BACKEND DEVICES')
    power_type = fields.Boolean(string='POWER')
    backhaul_fibre_type = fields.Boolean(string='BACKHAUL FIBER')
    backhaul_microwave_type = fields.Boolean(string='BACKHAUL MICROWAVE')
    access_fibre_type = fields.Boolean(string='ACCESS FIBER')
    access_radio_type = fields.Boolean(string='ACCESS RADIO')
    service_impact = fields.Char(string='SERVICE IMPACT')
    services = fields.Char(string='SERVICES')
    pop_affected = fields.Char(string='POPS AFFECTED')
    duration_close = fields.Char(string='Duration', compute=_compute_close_duration)

    #activation form
    olt_id = fields.Many2one(related='partner_id.olt_id',  string='OLT')
    gpon_level = fields.Char(string='GPON Port')
    power_level_id = fields.Char(string='Power Level')
    idu_serial_no = fields.Char(string='IDU SerialNumber')
    wifi_ssid = fields.Char(string='Wifi SSID')
    splitter_box_code = fields.Char(string='Splitter Box Code')
    region_id = fields.Many2one(related='partner_id.region_id', string='Region')
    installation_fse_id = fields.Many2one('res.users',string='Installation FSE')
    installation_approver_id = fields.Many2one('res.users',string='Installation Approval')
    wireless_technology = fields.Char(string='Wireless Technology')
    rssi_id = fields.Char(string='RSSI')
    radio_ip_addr = fields.Char(string='Radio IP Address')
    indoor_ip_address = fields.Char(string='Indoor IP Address')
    ap_ip_address = fields.Char(string='AP IP Address')
    radio_model = fields.Char(string='Radio Model(microwave,MK,UB,Vjjt etc)')
    vlan_act = fields.Char(string='Vlan')
    comment_activation = fields.Char(string='Comment')

    #Quality Assurance
    confirmed_rssi_id = fields.Char( string='Confirmed RSSI')
    confirmed_throughput = fields.Char(string='Confirmed Throughput')
    confirmed_power_level_id = fields.Char(string='Confirmed Power Level')
    bandwidth_test = fields.Selection([('yes', 'Yes'),('no', 'No')], string='Bandwidth Test (Pass or Failed)')
    earthen = fields.Selection([('yes', 'Yes'),('no', 'No')], string='Earthen')
    surge_protector = fields.Selection([('yes', 'Yes'),('no', 'No')], string='Surge Protector')
    indoor_picture = fields.Selection([('yes', 'Yes'),('no', 'No')],string='Indoor Picture')
    outdoor_picture = fields.Selection([('yes', 'Yes'),('no', 'No')],string='Outdoor Picture')
    cable_part_picture = fields.Selection([('yes', 'Yes'),('no', 'No')],string='Cable Part Picture')

    #Call Log
    call_type = fields.Selection([('inbound_support', 'Inbound Support'),('inbound_enquiry', 'Inbound Enquiry'),('outbound_retention', 'Outbound Retention')], string='Call Type')
    churned_date = fields.Date(string='Churned Date')
    no_of_month = fields.Integer(string='No. of Month')
    reason_call_log = fields.Text(string='Reason')
    comment_call_log = fields.Text(string='Comment/Feedback')
    reactivation_date = fields.Date(string='Reactivation Date')
    region_call_id = fields.Many2one('kkon.region', string='Region')
    complaint_type_id = fields.Many2one('kkon.complaint.type', string='Complaint Type')
    non_cust_name = fields.Char(string='Name')
    non_cust_address = fields.Char(string='Address')
    non_cust_client_id = fields.Char(string='Client ID')
    non_cust_email = fields.Char(string='Email')
    non_cust_phone = fields.Char(string='Phone')
    source_call = fields.Selection(
        [('call', 'Call'), ('email', 'Email'),
         ('chat', 'Chat'),('web', 'Web'),('eservice', 'Eservice'),('epclekki', 'EPC Lekki'),('twitter', 'Twitter'),('googlereview', 'Google Review'),('whatsapp', 'Whatsapp')], string='Source')


    #Change Request
    is_service_relocation = fields.Selection([('yes', 'Yes'),('no', 'No')], string='Is Service Relocation',  tracking=True)
    elapsed_hours_first = fields.One2many('kkon.elapsed.hour.first','ticket_id', string='First Escalation Elapsed Hours')
    elapsed_hours_second = fields.One2many('kkon.elapsed.hour.second', 'ticket_id', string='Second Escalation Elapsed Hours')
    elapsed_hours_third = fields.One2many('kkon.elapsed.hour.third', 'ticket_id', string='Third Escalation Elapsed Hours')
    total_elapsed_hours_first = fields.Integer(compute=_compute_total_elapsed_hours_first, string="First Escalation Total Elapsed Hours", store=True)
    total_elapsed_hours_second = fields.Integer(compute=_compute_total_elapsed_hours_second, string="Second Escalation Total Elapsed Hours", store=True)
    total_elapsed_hours_third = fields.Integer(compute=_compute_total_elapsed_hours_third, string="Third Escalation Total Elapsed Hours", store=True)
    area_change_request_id = fields.Many2one('kkon.area', string="Area", tracking=True)
    updown_grade_type = fields.Selection([('upgrade', 'Upgrade'), ('downgrade', 'Downgrade'),('disconnect', 'Disconnect'),('reconnection', 'Reconnection'),('relocation', 'Relocation'),('voip', 'Voip')], string='Change Request Type')
    product_curr_id = fields.Many2one('product.product',string='Current Package')
    product_new_id = fields.Many2one('product.product', string='New Package')
    bandwidth_current = fields.Char(string='Current Bandwidth')
    bandwidth_new = fields.Char(string='New Bandwidth')
    address_old = fields.Char(string='Old Address')
    address_new = fields.Char(string='New Address')
    address_ip_current = fields.Char(string='Current IP Address')
    adddress_ip_new = fields.Char(string='New IP Address')
    done_date = fields.Datetime(string='Completed Date')
    integration_date = fields.Datetime(string='Finalized Date')

    last_log_datetime = fields.Datetime(string='Last Logged datetime')
    last_log_user_id = fields.Many2one('res.users',string='Last Logged User')
    last_log_message = fields.Html(string='Last Log Message')
    is_upcountry = fields.Boolean(string='Up Country Transaction')

    is_area_manager_email_sent  = fields.Boolean(string='Is Area Manager Email Sent')
    is_regional_manager_hcx_email_sent = fields.Boolean(string='Is Regional Manager/HCX Email Sent')
    is_cto_rm_hcx_email_sent = fields.Boolean(string='Is CTO/RM/HCX Email Sent')
    is_bpsq_cto_manager_email_sent = fields.Boolean(string='Is BPSQ/CTO Email Sent')
    is_bpsq_cto_manager1_email_sent = fields.Boolean(string='Is BPSQ/CTO 1 Email Sent')
    is_bpsq_md_manager_email_sent = fields.Boolean(string='Is MD/BPSQ Email Sent')

    is_hcx_email_sent = fields.Boolean(string='Is HCX Email Sent')
    is_hcx1_email_sent = fields.Boolean(string='Is HCX 1 Email Sent')
    is_hcx_team_lead_email_sent = fields.Boolean(string='Is HCX/Teamlead')
    is_hcx2_email_sent = fields.Boolean(string='Is HCX 2 Email Sent')
    is_bpsq_md_manager1_email_sent = fields.Boolean(string='Is MD/BPSQ 1 Email Sent')

    is_cx_email_sent = fields.Boolean(string='Is CX')
    is_team_lead_email_sent = fields.Boolean(string='Is Teamlead')
    is_hcx3_email_sent = fields.Boolean(string='Is HCX 3 Email Sent')
    is_bpsq_hcx_email_sent = fields.Boolean(string='Is BPSQ/HCX')



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    #
    # 
    # def write(self, vals):
    #     is_partner = vals.get('partner_id', False)
    #     if is_partner and self.is_advance_invoice:
    #         raise UserError(_('Sorry, you are not allowed to change the customer, for the advance payment invoice'))
    #
    #     res = super(AccountInvoice, self).write(vals)
    #     return res

    
    def unlink(self):
        for rec in self:
            if rec.is_installation_invoice :
                if self.env.user not in rec.installation_ticket_id.initiator_ticket_group_id.sudo().user_ids:
                    raise UserError('Sorry, you cannot delete an installation invoice')
            if rec.is_eservice_invoice :
                raise UserError('Sorry, Eservice Invoice Cannot be deleted')
        return super(AccountInvoice,self).unlink()

    is_installation_invoice = fields.Boolean(string='Is Installation Invoice')
    installation_ticket_id = fields.Many2one('kin.ticket',string='Installation Ticket')


class Message(models.Model):
    _inherit = 'mail.message'

    
    def create(self, values):
        res = super(Message,self).create(values)
        if isinstance(values['model'], bool):
            return res
        if 'kin.ticket' in values['model']:
            res_id = values['res_id']
            ticket_obj = self.env['kin.ticket'].browse(res_id)
            ticket_obj.last_log_datetime = datetime.today()
            ticket_obj.last_log_user_id = ticket_obj.env.user
            ticket_obj.last_log_message = values['body']
        return res