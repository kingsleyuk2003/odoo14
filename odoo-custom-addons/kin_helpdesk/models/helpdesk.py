# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017-2021  Kinsolve Solutions
# Copyright 2017-2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError

class ResUsers(models.Model):
    _inherit = 'res.users'

    user_ticket_group_ids = fields.Many2many('user.ticket.group', 'user_ticket_group_rel', 'user_id','user_ticket_group_id', string='User Ticket Groups', ondelete='restrict')


class UserGroups(models.Model):
    _name = 'user.ticket.group'

    @api.model
    def create(self, vals):
        self.clear_caches()
        return super(UserGroups,self).create(vals)

    # Clear cache for Record Rules to take effect without restarting the server, for many2many fields. It does not apply to other type of fields
    
    def write(self, vals):
        # Record rules based on many2many relationship were not applied when many2many fields values were modified.
        #This not affect unlink/deletion of records, so no need to clear cache for unlink()
        self.clear_caches()  # ref: https://www.odoo.com/forum/help-1/question/force-odoo-to-delete-cache-81650
        return super(UserGroups,self).write(vals)

    name = fields.Char(string='User Ticket Group')
    user_ids = fields.Many2many('res.users', 'user_ticket_group_rel', 'user_ticket_group_id', 'user_id', string='Users', ondelete='restrict')
    company_id = fields.Many2one('res.company',string='Company')
    pre_state = fields.Selection(
        [('draft', 'Draft'), ('new', 'Open'), ('progress', 'Work In Progress'), ('done', 'Done'), ('closed', 'Closed'),
         ('cancel', 'Cancelled')], string="Pre-Status", default='draft')


class sla(models.Model):
    _name = "kin.sla"
    _description = "Service Level Agreement"

    name = fields.Char(string='SLA Policy Name')

class HelpDeskTeam(models.Model):
    _name = "kin.helpdesk.team"
    _description = "Help Desk"

    name = fields.Char('Name', required=True)
    color = fields.Integer('Color Index')

    _sql_constraints = [
            ('name_uniq', 'unique (name)', "Help Desk Name already exists !"),
    ]

class TicketStage(models.Model):
    _name = "kin.ticket.stage"
    _description = "Ticket Stage"

    name = fields.Char('Name',required=True)
    categ_id = fields.Many2one('kin.ticket.category',string='Ticket Category')
    ticket_ids = fields.One2many('kin.ticket','stage_id',string='Tickets')
    active = fields.Boolean(string='Active',default=True)
    sequence = fields.Integer('sequence',default=10)




class TicketCategory(models.Model):
    _name = "kin.ticket.category"
    _description = "Ticket Category"

    name = fields.Char('Name', required=True)
    description = fields.Char(string='Description')
    code = fields.Char(string="code")
    ticket_stage_ids = fields.One2many('kin.ticket.stage','categ_id',string='Ticket Stages')


    _sql_constraints = [
            ('name_uniq', 'unique (name)', "Category already exists !"),
    ]

    # service_category = fields.Selection([
    #     ('installation', 'Installation'),
    #     ('support', 'Support'),
    #     ('survey', 'Survey')
    #
    # ], string='Service Category')


class TicketCost(models.Model):
    _name = 'kin.ticket.cost'

    @api.model
    def create(self, vals):

        analytic_line_obj = self.env['account.analytic.line']
        ticket_obj = self.env['kin.ticket']

        analytic_account_id = vals.get('analytic_account_id',False)
        ticket_id = vals.get('ticket_id',False)
        ticket_cost = vals.get('ticket_cost',False)

        if analytic_account_id and ticket_id and ticket_cost:
            ticket = ticket_obj.browse(ticket_id)
            ticket_name = ticket.name
            ticket_id = ticket.ticket_id
            data = {
                'name' : ticket_name + ' - ' + ticket_id,
                'account_id' : analytic_account_id ,
                'amount' : ticket_cost,
            }
            line_id = analytic_line_obj.create(data)
            ticket.analytic_line_id = line_id.id

        res = super(TicketCost, self).create(vals)
        res.analytic_line_id = line_id.id
        return res

    
    def write(self, vals):
        ticket_cost = vals.get('ticket_cost', False)
        line = self.analytic_line_id or False
        if ticket_cost and line:
            self.analytic_line_id.amount = ticket_cost

        res = super(TicketCost, self).write(vals)
        return res

    
    def unlink(self):
        for rec in self:
            rec.analytic_line_id.unlink()
        return super(TicketCost, self).unlink()

    # 
    # def _default_user(self):
    #     return self.env.context.get('user_id', self.env.user.id)

    analytic_account_id = fields.Many2one('account.analytic.account', string='Cost/Analytic Account.')
    analytic_line_id = fields.Many2one('account.analytic.line',string='Analytic Line')
    ticket_cost = fields.Monetary(string='Cost')
    ticket_id = fields.Many2one('kin.ticket',string='Ticket',ondelete='cascade')
    # user_id = fields.Many2one('res.users', string='User', default=_default_user)
    # company_id = fields.Many2one(related='user_id.company_id', string='Company', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string="Currency",  default=lambda self: self.env.user.company_id.currency_id.id)


class Ticket(models.Model):
    _name = 'kin.ticket'
    _description = "Help Desk Ticket"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'ticket_id desc'

    # @api.onchange('stage_id')
    # def set_to_first_stage(self):
    #     first_stage =  self.env['kin.ticket.category'].search(['stage_id.id','=',self.stage_id])
    #     self.stage_id  = first_stage

    def send_email(self, grp_name, subject, msg):
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref(grp_name)
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)
        if partn_ids:
            # self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partn_ids, subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))


    def reassign_ticket(self,grp):
        self.state = grp.pre_state
        self.user_ticket_group_id = grp
        # send email to the Assigned users too
        partn_ids = []
        user_names = ''
        users = grp.sudo().user_ids
        msg = 'The Ticket (%s) with description (%s), has been Reassigned to %s by %s ' % (
            self.ticket_id, self.name,  grp.name,self.env.user.name)

        for user in users:
            if user.is_group_email:
                user_names += user.name + ", "
                partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_post( body=_(msg), subject='%s' % msg, partner_ids=partn_ids ,subtype_xmlid='mail.mt_comment')

        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))



    def btn_ticket_open(self):
        self.state = 'new'
        self.open_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.user_id = self.env.user

        # send email to the Assigned users too
        partn_ids = []
        user_names = ''
        eng_users = self.user_ticket_group_id.sudo().user_ids
        msg = 'The Ticket (%s) with description (%s), has been Opened by %s' % (
            self.ticket_id, self.name, self.env.user.name)
        for user in eng_users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_post(
               body= _(msg),
                subject='%s' % msg, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment')

        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        group_name = 'kin_helpdesk.group_helpdesk_receive_open_ticket_email'
        msg = 'The Ticket (%s) with description (%s), has been Opened by %s' % (self.ticket_id, self.name, self.env.user.name)
        subject = msg
        self.send_email(group_name,subject,msg)



    
    def btn_ticket_progress(self):
        self.state = 'progress'
        group_name = 'kin_helpdesk.group_helpdesk_receive_in_progress_ticket_email'
        msg = 'The Ticket (%s) with description (%s), is in progress by %s' % (
            self.ticket_id, self.name, self.env.user.name)
        subject = msg
        self.send_email(group_name, subject, msg)


    
    def btn_ticket_done(self):
        self.state = 'done'
        self.done_ticket_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        group_name = 'kin_helpdesk.group_helpdesk_receive_done_ticket_email'
        msg = 'The Ticket (%s) with description (%s), has been Done by %s' % (
            self.ticket_id, self.name, self.env.user.name)
        subject = msg
        self.send_email(group_name, subject, msg)


    
    def btn_ticket_close(self):
        self.state = 'closed'
        self.closed_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self._compute_time_spent()

        group_name = 'kin_helpdesk.group_helpdesk_receive_close_ticket_email'
        msg = 'The Ticket (%s) with description (%s), has been Closed by %s' % (
        self.ticket_id, self.name, self.env.user.name)
        subject = msg
        self.send_email(group_name, subject, msg)


    
    def btn_ticket_reset(self):
        self.state = 'draft'
        self.open_date = self.closed_date = self.time_spent = False

        group_name = 'kin_helpdesk.group_helpdesk_receive_reset_ticket_email'
        msg = 'The Ticket (%s) with description (%s), has been Reset by %s' % (
            self.ticket_id, self.name, self.env.user.name)
        subject = msg
        self.send_email(group_name, subject, msg)

    
    def btn_ticket_cancel(self):
        self.state = 'cancel'

        group_name = 'kin_helpdesk.group_helpdesk_receive_cancel_ticket_email'
        msg = 'The Ticket (%s) with description (%s), has been Cancelled by %s' % (
            self.ticket_id, self.name, self.env.user.name)
        subject = msg
        self.send_email(group_name, subject, msg)


    def read(self, fields=None, load='_classic_read'):
        res =  super(Ticket, self).read(fields=fields, load=load)
        self._compute_time_elapsed()
        return res


    def unlink(self):
        for ticket in self:
            if ticket.state not in 'draft':
                raise UserError(_("Cannot delete ticket that is not in draft state."))
            ticket.ticket_cost_ids.unlink()
        return super(Ticket, self).unlink()


    @api.model
    def create(self,vals):
        vals['ticket_id'] = self.env['ir.sequence'].get('tick_id_code')
        vals['assigned_date'] = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        ticket_obj = super(Ticket,self.sudo()).create(vals)



        if vals.get('partner_id',False)  :
            user_ids = []
            partner_ids = []
            partner_ids.append(ticket_obj.partner_id.id)
            #ticket_obj.message_subscribe(partner_ids=partner_ids)
            #ticket_obj.message_subscribe_users(user_ids=user_ids)
            #inv_obj.message_post( body=_('A New Ticket has been Opened with Ticket No: %s.') % (ticket_obj.ticket_id),subject='A New Ticket ahs been created for your request', subtype_xmlid='mail.mt_comment', force_send=False)

        return ticket_obj

    def _compute_time_spent(self):
        for ticket in self :
            if  ticket.open_date and ticket.closed_date :
                closed_date = ticket.closed_date
                open_date = ticket.open_date
                date_diff = str(closed_date - open_date)
                ticket.time_spent = date_diff

    def _compute_time_elapsed(self):
        for ticket in self :
            if  ticket.open_date and not ticket.closed_date :
                today_date = datetime.strptime(datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT), DEFAULT_SERVER_DATETIME_FORMAT)
                open_date = ticket.open_date
                date_diff =  str(today_date - open_date)
                ticket.time_elapsed = date_diff

    def _compute_duration(self):
        for ticket in self :
            if ticket.expected_finish_date and ticket.assigned_date :
                expected_finish_date = datetime.strptime(ticket.expected_finish_date , DEFAULT_SERVER_DATETIME_FORMAT)
                assigned_date = datetime.strptime(ticket.assigned_date , DEFAULT_SERVER_DATETIME_FORMAT)
                date_diff =  str(expected_finish_date - assigned_date)
                ticket.duration =  date_diff

    def get_expected_days_interval(self):
        interval = self.env['ir.config_parameter'].sudo().get_param('kin_helpdesk.expected_finished_date_interval',default=0)
        return datetime.now() + relativedelta(days=+int(interval))

    name = fields.Char(string="Subject",required=1)
    partner_id = fields.Many2one('res.partner',string='Customer')
    partner_name = fields.Char( string="Customer's Name")
    email = fields.Char(string ='Email')
    mobile = fields.Char(string ='Mobile')
    phone = fields.Char(string ='Phone')
    description = fields.Html(string='Description')
    assigned_date = fields.Datetime(string='Assigned Date')
    open_date = fields.Datetime(string='Open Ticket Date')
    closed_date = fields.Datetime(string='Closed Ticket Date')
    time_elapsed = fields.Char(string='Time Elapsed',readonly=1)
    time_spent = fields.Char(string='Time Spent to Close Ticket',readonly=1)
    expected_finish_date = fields.Datetime(string='Expected Finished Date', default=get_expected_days_interval)
    done_ticket_date = fields.Datetime(string='Done Date')
    duration = fields.Char(string='Duration(days)',compute=_compute_duration, store=True)
    priority = fields.Selection([('0','low'), ('1','Medium'),('2','High'),('3','Critical')], default=0, string='Priority', select=True, store=True)
    attachment = fields.Binary(string='Attachment',  attachment=True)
    ticket_id = fields.Char(string='Ticket ID')
    user_id = fields.Many2one('res.users',string='Support Person',default=lambda self: self.env.user.id)
    category_id = fields.Many2one('kin.ticket.category',string='Ticket Category')
    ticket_type = fields.Selection([('issue','Issue'), ('question','Question')], string='Ticket Type', select=True)
    user_ticket_group_id = fields.Many2one('user.ticket.group',string='Assigned User Group',ondelete='restrict')
    #engineer_ids = fields.Many2many('res.users',string='Engineers/Users',related='user_ticket_group_id.user_ids',store=True)
    ticket_cost_ids = fields.One2many('kin.ticket.cost','ticket_id',string='Costs')
    state = fields.Selection([('draft','Draft'),('new','Open'),('progress','Work In Progress'), ('done','Done'),('closed','Closed'),('cancel','Cancelled')],default='draft', tracking=True)
    stage_id = fields.Many2one('kin.ticket.stage',string='Stages',tracking=True)
    colour = fields.Integer('Colour')
    ticket_company_id = fields.Many2one('res.company',string='Ticket Company', select=True, default=lambda self: self.env.user.company_id)


class ResPartner(models.Model):
    _inherit ='res.partner'

    
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


    ticket_ids = fields.One2many('kin.ticket','partner_id', string='Tickets')
    ticket_count = fields.Integer(compute="_compute_ticket_count", string='# of Ticket', copy=False, default=0)