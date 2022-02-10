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
import pytz

class UserGroups(models.Model):
    _inherit = 'user.ticket.group'
    _description = 'User Ticket Group'

    is_eng_default = fields.Boolean(string='Is Assigned Team Default')
    is_intg_default = fields.Boolean(string='Is Finalized Default')
    is_survey_group_default_csc = fields.Boolean(string='Is Survey Group Default')
    is_installation_group_default_csc = fields.Boolean(string='Is Installation Group Default for CSC')
    is_maint_default = fields.Boolean(string='Is Maintenance Close Team Default')
    is_csc_group = fields.Boolean(string='Is CSC Group')

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
        return super(Area, self).create(vals)


    name = fields.Char(string='Area')
    area_manager_id = fields.Many2one('res.users',string="Area Manager")
    area_manager_id = fields.Many2one('res.users', string="Area Manager")
    sales_person_id = fields.Many2one('res.users', string="Sales Person")
    user_ticket_group_id = fields.Many2one('user.ticket.group', string='Engineer User Ticket Group')
    prefix = fields.Char(string='Prefix')
    sequence_id = fields.Many2one('ir.sequence', string="Sequence",ondelete="restrict")
    is_others = fields.Boolean(string="Is Others", default=False)

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
    _description = 'Elepsed Hour First'

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

class Ticket(models.Model):
    _inherit = 'kin.ticket'
    _rec_name = 'ticket_id'


    @api.onchange('area_customer_id')
    def _set_assigned_user_group_from_area(self):
        for rec in self:
            user_ticket_group_id = rec.area_customer_id.user_ticket_group_id
            if user_ticket_group_id :
                rec.user_ticket_group_id =user_ticket_group_id


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


    def send_escalation_msg(self,partner_ids,subject,msg):
        if partner_ids:
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partner_ids, subtype_xmlid='mail.mt_comment', force_send=False)
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
        if self.finalized_date:
            user_tz_obj = pytz.timezone(self.env.context.get('tz') or 'Africa/Lagos')
            localize_tz = pytz.utc.localize
            finalized_date_format = localize_tz(datetime.strptime(self.finalized_date, '%Y-%m-%d %H:%M:%S')).astimezone(
                user_tz_obj).strftime('%d-%m-%Y %H:%M:%S')
            subject = 'Finalized Service Relocation Ticket Alert (%s) for ticket with ID: %s' % (esc_type, self.ticket_id)
            msg = _(
                'The is to bring to your attention, that the service relocation ticket (%s) with subject (%s), which has been finalized on %s, has not been closed. Kindly attend to the Service relocation ticket and ensure it is closed, to avoid further escalation') % (
                      self.ticket_id, self.name, finalized_date_format)

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
            [('finalized_date', '<', today), ('is_service_relocation', '=', 'yes'),
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
                    datetime.strptime(ticket.finalized_date, '%Y-%m-%d %H:%M:%S')).astimezone(
                    user_tz_obj).day
                start_hour = localize_tz(
                    datetime.strptime(ticket.finalized_date, '%Y-%m-%d %H:%M:%S')).astimezone(
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
            [('finalized_date', '<', today), ('is_service_relocation', '=', 'yes'),
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
                    msg = _('The Installation Ticket (%s) with subject (%s), having expected finished date as %s, is overdue for closure, by %s hours') % (ticket.ticket_id,ticket.name, exp_date_format,date_diff)
                    self.message_post(
                        body=msg,
                        subject=msg, partner_ids=partn_ids,
                        subtype_xmlid='mail.mt_comment', force_send=False)

            return True


    def btn_ticket_progress(self):
        if self.category_id == self.env.ref('fibernet.maintenance') and self.state == 'new':
            raise UserError(_('CTO has to approve the maintenance ticket before it can commence work'))
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



    def btn_ticket_open(self):
        if not self.category_id or not self.user_intg_ticket_group_id :
            raise UserError(_('Contact the Admin to set the default Finalized group'))

        if self.category_id  in  (self.env.ref('fibernet.support'),self.env.ref('fibernet.updown_grade')) and not self.partner_id.ref:
            raise UserError(_('Set the Customer Client ID on the customers database for this ticket to be opened'))
        elif self.category_id == self.env.ref('fibernet.maintenance'):
            maint_close_group = self.env['user.ticket.group'].search([('is_maint_default', '=', True)], limit=1)
            if not maint_close_group:
                raise UserError(_(
                    'Please contact the Admin to set the Maintenance Close Group '))
            if not self.base_station_maint_id:
                raise UserError(_('Please Select the Base Station to be maintained in the Maintenance Form below'))
            self.user_maint_ticket_group_id = maint_close_group
        else:
            self.user_maint_ticket_group_id = False

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


        #Send email to the customer for opening the installation ticket
        partner_id = self.partner_id
        if partner_id and self.category_id == self.env.ref('fibernet.installation'):
            if not partner_id.email:
                raise UserError(
                    'Kindly set the email for the %s with client id %s, in the customers database, before this ticket can be opened' % (
                    partner_id.name, partner_id.ref or ''))

            msg = 'Dear %s, <p>This is to acknowledge the receipt of your payment for (Package-%s) Broadband service. </p> An installation ticket with the ID: %s has been opened for your installation. <p> Your Service ID : %s (this will be required for future communication).</p> <p> Kindly note that installation takes 3 to 7 working days. </p> <p> For further enquiries and assistance, please feel free to contact us through any of the following channels:</p><p><ul class=o_timeline_tracking_value_list><li>Calls: +2349083301363</li><li>Email: csc@fibernet.ng</li></ul></p><p>Please visit our website <a href=https://fibernet.ng/ >https://fibernet.ng/</a> for other terms and conditions.</p><p>We appreciate your interest in Fibernet Broadband and we hope you will enjoy our partnership as we provide you a reliable and steady internet connectivity.</p><p> Regards,</p>Customer Service Center</p>' % \
                  (
                      partner_id.name, self.sudo().product_id.name, self.ticket_id, partner_id.ref)
            self.message_follower_ids.unlink()
            mail_obj = self.message_post(
                body=_(msg),
                subject='%s Opened Installation Ticket Notification for %s' % (
                    self.sudo().product_id.name, partner_id.name), partner_ids=[partner_id.id],subtype_xmlid='mail.mt_comment', force_send=False)
            user_names += partner_id.name + ", "
            mail_obj.email_from = 'csc@fibernet.ng'
            mail_obj.reply_to = 'csc@fibernet.ng'
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        elif partner_id and  self.category_id in [self.env.ref('fibernet.support'),self.env.ref('fibernet.updown_grade')]:
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
                open_date = ticket.open_date
                now_date = datetime.strptime(datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),DEFAULT_SERVER_DATETIME_FORMAT)
                date_diff =  str(now_date - open_date)
                ticket.duration_close =  date_diff


    def action_view_order(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Order'),
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.order_id])],
            'target': 'new'
        }

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

    
    def btn_ticket_reset(self):
        for rec in self:
            rec.invoice_id.unlink()
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

        if self.category_id in (self.env.ref('fibernet.support'), self.env.ref('fibernet.survey'), self.env.ref('fibernet.maintenance')) :
            self.state = "finalized"
            self.finalized_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            # email ticket opener users
            partn_ids = []
            user_names = ''
            msg = 'The Ticket (%s) with description (%s), has been completed and  finalized by %s, you may now close the ticket' % (
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


        #     if not self.root_cause or  not self.resolution :
        #         raise UserError(_('Please Set the Root Cause and Resolution in the Other Information Tab'))

        partn_ids = []
        user_names = ''
        if self.category_id == self.env.ref('fibernet.maintenance'):
            if not self.backend_devices_type and not self.power_type and not self.backhaul_fibre_type and not self.backhaul_microwave_type and not self.access_fibre_type and not self.access_radio_type:
                raise UserError(_('Please select at least a TYPE in the Maintenance TAB'))
            init_users = self.initiator_ticket_group_id.sudo().user_ids
            for user in init_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_ids.append(user.partner_id.id)


        msg = 'The Ticket (%s) with description (%s), has been Done by %s' % (
        self.ticket_id, self.name, self.env.user.name)

        if partn_ids:
            self.message_follower_ids.unlink()
            self.message_post(
               body= _(msg),
                subject='%s' % msg, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)

        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
        self.done_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return super(Ticket,self).btn_ticket_done()

    
    def btn_ticket_close(self):

        if self.category_id == self.env.ref('fibernet.installation') and self.state != 'finalized' :
            raise UserError('You cannot close an installation ticket that is not yet finalized')

        if self.category_id == self.env.ref('fibernet.installation') and self.order_id :
            self.order_id.is_installation_ticket_close = True

            #set partner parameters
            self.partner_id.status = self.status
            self.partner_id.activation_date = self.activation_date

            #create invoice
            if self.order_id :
                if self.invoice_id :
                    raise UserError('Sorry, this ticket has been previously closed and invoice created. Please refresh your browser')
                invoice = self.create_customer_invoice(self.order_id)

            # send email
            self.send_email('fibernet.group_ticket_installation_close_notify',subject='An Installation Ticket has been closed',
            msg = _('The Installation Ticket %s has been closed for the order id - %s, from %s') % (
                self.name, self.order_id.name, self.env.user.name))


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
            user_ids = []
            group_obj = self.env.ref('fibernet.group_ticket_survey_close_notify')
            user_names = ''
            for user in group_obj.sudo().users:
                user_names += user.name + ", "
                user_ids.append(user.partner_id.id)

                self.send_email('fibernet.group_ticket_survey_close_notify',
                                subject='The Survey Ticket has been closed',
                                msg=_(
                    'The Survey Ticket %s has been closed for the order id - %s, from %s') % (
                    self.name, self.order_id.name,self.env.user.name))

        elif self.category_id == self.env.ref('fibernet.updown_grade'):
            # send email
            self.send_email('fibernet.group_ticket_updown_close_notify',
                            subject='The Change Request Ticket has been closed',
                            msg=_(
                    'The Change Request Ticket %s has been closed by %s') % (
                    self.name,self.env.user.name))

        return super(Ticket,self).btn_ticket_close()





    #CTO approves maintenance ticket
    def btn_ticket_maint_approve(self):
        if self.category_id != self.env.ref('fibernet.maintenance') :
            raise UserError(_('Sorry, you may rather Click the Done button. This is not a maintenance ticket'))

        self.state = 'maint_approve'
        if self.category_id == self.env.ref('fibernet.maintenance') :
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


        grp_name = 'fibernet.group_helpdesk_receive_maint_ticket_email'
        subject = 'The Maintenance Ticket (%s) with description (%s), has been approved by %s from the CTO' % (
            self.ticket_id, self.name, self.env.user.name)
        msg = subject
        self.send_email(grp_name, subject, msg)

    


    
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



    
    def action_ticket_maint_reject(self,msg):
        if self.category_id != self.env.ref('fibernet.maintenance') :
            raise UserError(_('Sorry, you may rather Click the Done button. This is not a maintenance ticket'))

        self.state = 'draft'
        self.maint_disapprove_by = self.env.user
        self.maint_disapprove_date = datetime.today()
        self.maint_disapprove_msg = msg

        if self.category_id == self.env.ref('fibernet.maintenance'):

            partn_ids = []
            user_names = ''
            mesg = 'The Maintenance Ticket (%s) with description (%s), has been Declined by %s from the CTO  with reason: (%s)' % (
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
                    _(mesg),
                    subject='%s' % mesg, partner_ids=partn_ids)

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

            if not self.expiration_date :
                raise UserError('Please set the expiration date for this service in the activation tab below')

            #push new customer to selfcare
            if not self.order_id :
                raise UserError('No Sales Order for this Ticket')

            if self.order_id.amount_balance:
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

            self.partner_id.amount = self.order_id.amount_total
            self.partner_id.action_create_customer_selfcare()

            self.partner_id.status = 'active'
            self.partner_id.activation_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
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
            area_id =  vals.get('area_customer_id', False)
            if area_id and not self.partner_id.ref  :
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

         #update the change request new values
        if self.state == 'closed' and self.category_id == self.env.ref('fibernet.updown_grade'):
            self.partner_id.product_id = self.product_new_id
            self.partner_id.bandwidth = self.bandwidth_new
            self.partner_id.street = self.address_new
            self.partner_id.ip_address = self.adddress_ip_new

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
    order_count = fields.Integer(compute="_compute_order_count", string='# of CRMs', copy=False, default=0)
    crm_id = fields.Many2one('crm.lead', string='CRM')
    crm_count = fields.Integer(compute="_compute_crm_count", string='# of CRMs', copy=False, default=0)
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_count = fields.Integer(compute="_compute_invoice_count", string='# of Invoices', copy=False, default=0)

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
    access_confirmation = fields.Char(string="Confirmation of access to the location")
    installation_constraint = fields.Text(string="Constraints that could delay the installation")
    survey_attachment = fields.Binary(string="Survey Attachment Picture/FIle")

    root_cause = fields.Text(string='Root Cause')
    resolution = fields.Text(string='Resolution')
    call_type_support = fields.Selection([('inbound_support', 'Inbound Support'), ('inbound_enquiry', 'Inbound Enquiry'),
                                  ('outbound_retention', 'Outbound Retention')], string='Support Call Type')
    source_support = fields.Selection(
        [('call', 'Call'), ('email', 'Email'),
         ('chat', 'Chat'),('web', 'Web')], string='Source')
    complaint_type_support_id = fields.Many2one('complaint.type', string='Complaint Type')
    done_ticket_date = fields.Datetime(string='Resolved Ticket Date')

    maint_disapprove_msg = fields.Text(string='Declined Reason')
    maint_disapprove_by = fields.Many2one('res.users', string='Declined By')
    maint_disapprove_date = fields.Datetime(string='Declined Date and Time')

    opener_disapprove_msg = fields.Text(string='Ticket Opener Rejection Reason')
    opener_disapprove_by = fields.Many2one('res.users', string='Rejected By')
    opener_disapprove_date = fields.Datetime(string='Rejection Date and Time')

    finalized_reject_msg = fields.Text(string='Finalized Rejection Reason')
    finalized_reject_by = fields.Many2one('res.users',string='Rejected By')
    finalized_rejection_date = fields.Datetime(string='Rejection Date and Time')
    user_intg_ticket_group_id = fields.Many2one('user.ticket.group',default=get_default_intg_group, string='Finalized User Group',ondelete='restrict')
    initiator_ticket_group_id = fields.Many2one('user.ticket.group',default=get_initiator_group,string='Ticket Opener Group')
    user_ticket_group_id = fields.Many2one('user.ticket.group', default=get_default_eng_group, string='Assigned User Group')
    user_maint_ticket_group_id = fields.Many2one('user.ticket.group',string='Maintenance Ticket Close Group' )


    state = fields.Selection(
        [('draft', 'Draft'), ('new', 'Open'), ('maint_approve', 'Maint. Approved'), ('progress', 'Work In Progress'),('done', 'Completed'), ('finalized','Finalized'),('closed', 'Closed'),('cancel', 'Cancelled'),('archived', 'Archived')],
        default='draft', tracking=True)

    description = fields.Text(string='Incident Details')

    #SUrvey Form fields
    site_survey_form = fields.Binary(string='Site Survey Form', attachment=True)
    srf_form = fields.Binary(string='SRF Form', attachment=True)
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
    duration_maint = fields.Char(string='DURATION',compute=_compute_duration_maint, store=True)
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


    #Call Log and Request
    prospect_name = fields.Char(string='Prospect Name')
    prospect_address = fields.Char(string='Prospect Address')
    prospect_area_id = fields.Many2one('area',string='Prospect Area')
    prospect_email = fields.Char(string='Prospect Email')
    prospect_phone = fields.Char(string='Prospect Phone')
    prospect_id = fields.Many2one('prospect', string ='Prospect')
    others_sales_person_id = fields.Many2one('res.users',string='Sales Person')
    is_others = fields.Boolean(related='prospect_area_id.is_others',string="Is Others")

    #Change Request
    is_service_relocation = fields.Selection([('yes', 'Yes'),('no', 'No')], string='Is Service Relocation',  tracking=True)
    elapsed_hours_first = fields.One2many('elapsed.hour.first','ticket_id', string='First Escalation Elapsed Hours')
    elapsed_hours_second = fields.One2many('elapsed.hour.second', 'ticket_id', string='Second Escalation Elapsed Hours')
    elapsed_hours_third = fields.One2many('elapsed.hour.third', 'ticket_id', string='Third Escalation Elapsed Hours')
    total_elapsed_hours_first = fields.Integer(compute=_compute_total_elapsed_hours_first, string="First Escalation Total Elapsed Hours", store=True)
    total_elapsed_hours_second = fields.Integer(compute=_compute_total_elapsed_hours_second, string="Second Escalation Total Elapsed Hours", store=True)
    total_elapsed_hours_third = fields.Integer(compute=_compute_total_elapsed_hours_third, string="Third Escalation Total Elapsed Hours", store=True)
    area_change_request_id = fields.Many2one('area', string="Area", tracking=True)
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
    finalized_date = fields.Datetime(string='Finalized Date')

    last_log_datetime = fields.Datetime(string='Last Logged datetime')
    last_log_user_id = fields.Many2one('res.users',string='Last Logged User')
    last_log_message = fields.Html(string='Last Log Message')
    category_code = fields.Char(related='category_id.code', string='Category Code')

    is_area_manager_email_sent = fields.Boolean(string='Is Area Manager Email Sent')
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

    assigned_eng_user_ids = fields.Many2many(related='user_ticket_group_id.user_ids', string='Engineers')
    show_alert_box = fields.Boolean(string="Show Alert Box")
    alert_msg = fields.Char(string='Alert Message')

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