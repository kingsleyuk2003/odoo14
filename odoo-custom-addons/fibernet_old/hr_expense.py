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
import  time
from odoo import tools, api

class ExpenseType(models.Model):
    _name = "kkon.expense.type"

    name = fields.Char(string='Expense Type')


class HRExpense(models.Model):
    _inherit = 'hr.expense'
    _order = 'date desc'

    def _get_url(self, module_name, menu_id, action_id, context=None):
        fragment = {}
        res = {}
        model_data = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fragment['menu_id'] = model_data.get_object_reference(module_name, menu_id)[1]
        fragment['model'] = 'hr.expense.group.kkon'
        fragment['view_type'] = 'form'
        fragment['action'] = model_data.get_object_reference(module_name, action_id)[1]
        query = {'db': self.env.cr.dbname}

        # for displaying tree view. Remove if you want to display form view
        #         fragment['page'] = '0'
        #         fragment['limit'] = '80'
        #         res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))

        # For displaying a single record. Remove if you want to display tree view

        fragment['id'] = context.get("expense_group_id")
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res




    
    def action_view_exp_group(self):
        expense_group_id = self.mapped('expense_group_id')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('kkon_modifications.action_hr_expense_group_kkon')
        list_view_id = imd.xmlid_to_res_id('hr_expense_group_tree_view_kkon')
        form_view_id = imd.xmlid_to_res_id('hr_expense_group_form_view_kkon')

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
        if len(expense_group_id) > 1:
            result['domain'] = "[('id','in',%s)]" % expense_group_id.id
        elif len(expense_group_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = expense_group_id.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    @api.depends('expense_group_id')
    def _compute_exp_group_count(self):
        for rec in self:
            rec.exp_group_count = len(rec.expense_group_id)

    
    @api.one
    def submit_expenses(self):
        if self.state != 'draft' :
            raise UserError('Sorry, you can only submit draft expenses')
        if self.employee_id.user_id != self.env.user:
            raise UserError('Please contact %s to submit this record' % (self.employee_id.name))

        res = super(HRExpense,self).submit_expenses()
        # if self.employee_id.parent_id and self.employee_id.parent_id.user_id :
        #     manager_id = self.employee_id.parent_id.user_id.partner_id
        #     self.message_post(
        #         _(
        #             'An Expense (%s), has been submitted and is awaiting Approval, from %s') % (
        #             self.name, self.env.user.name),
        #         subject='A New Expense has been submitted and is awaiting approval', partner_ids=[manager_id.id], subtype_xmlid='mail.mt_comment', force_send=False)
        #     self.env.user.notify_info('%s Will Be Notified by Email' % (manager_id.name))

        ctx = {}
        ctx.update({'expense_group_id': self.expense_group_id.id})
        the_url = self._get_url('kkon_modifications', 'menu_hr_expense_group_kkon', 'action_hr_expense_group_kkon',ctx)
        mail_template = self.env.ref('kkon_modifications.mail_templ_submit_expense_kkon')

        company_email = self.env.user.company_id.email
        requester_email = self.expense_group_id.user_id.partner_id.email
        requester_name = self.expense_group_id.user_id.partner_id.name

        user = self.line_manager_id.sudo().user_id
        ctx = {
            'system_email': company_email,
            'requester_name': requester_name,
            'requester_email': requester_email,
            'notify_person_email': user.partner_id.email,
            'notify_person_name': user.partner_id.name,
            'url': the_url,
            'currency_code':self.env.user.company_id.currency_id.symbol,

        }
        # mail_template.with_context(ctx).send_mail(self.id, force_send=False)
        # self.env.user.notify_info('%s Will Be Notified by Email' % (user.name))
        return res


    
    def reset_expenses(self):
        self.write({'refused_by':False,'refused_date':False,'refused_msg':False,'audited_by':False,'audited_date':False,'posted_by':False,'posted_date':False,'paid_by':False,'paid_date':False})
        res = super(HRExpense,self).reset_expenses()
        return res

    @api.one
    
    def refuse_expenses(self, reason):
        res = super(HRExpense,self).refuse_expenses(reason)
        employee_id = self.employee_id.user_id.partner_id

        self.refused_by = self.env.user
        self.refused_date = datetime.today()
        self.refused_msg = reason

        # self.message_post(
        #     _(
        #         'The Expense (%s), has been refused, by %s') % (
        #         self.name, self.env.user.name),
        #     subject='The Expense has been refused', partner_ids=[employee_id.id],
        #     subtype_xmlid='mail.mt_comment', force_send=False)
        # self.env.user.notify_info('%s Will Be Notified by Email' % (employee_id.name))
        ctx = {}
        ctx.update({'expense_group_id': self.expense_group_id.id})
        the_url = self._get_url('kkon_modifications', 'menu_hr_expense_group_kkon', 'action_hr_expense_group_kkon', ctx)
        mail_template = self.env.ref('kkon_modifications.mail_templ_refuse_kkon')

        company_email = self.env.user.company_id.email
        requester_email = self.refused_by.partner_id.email
        requester_name = self.refused_by.partner_id.name

        user = self.sudo().employee_id.user_id
        ctx = {
            'system_email': company_email,
            'requester_name': requester_name,
            'requester_email': requester_email,
            'notify_person_email': user.partner_id.email,
            'notify_person_name': user.partner_id.name,
            'url': the_url,
            'reason' : reason,
            'currency_code': self.env.user.company_id.currency_id.symbol,
        }
        mail_template.with_context(ctx).send_mail(self.id, force_send=False)
        self.env.user.notify_info('%s Will Be Notified by Email' % (user.name))
        return res

    @api.one
    
    def paid_expenses(self):
        res = super(HRExpense,self).paid_expenses()
        employee_id = self.employee_id.user_id.partner_id
        # self.message_post(
        #     _(
        #         'The Expense (%s), has been paid, by %s') % (
        #         self.name, self.env.user.name),
        #     subject='The Expense has been paid', partner_ids=[employee_id.id],
        #     subtype_xmlid='mail.mt_comment', force_send=False)
        # self.env.user.notify_info('%s Will Be Notified by Email' % (employee_id.name))
        self.paid_by = self.env.user
        self.paid_date = datetime.today()

        ctx = {}
        ctx.update({'expense_group_id': self.expense_group_id.id})
        the_url = self._get_url('kkon_modifications', 'menu_hr_expense_group_kkon', 'action_hr_expense_group_kkon', ctx)
        mail_template = self.env.ref('kkon_modifications.mail_templ_paid_kkon')

        company_email = self.env.user.company_id.email
        requester_email = self.paid_by.partner_id.email
        requester_name = self.paid_by.partner_id.name

        user = self.sudo().employee_id.user_id
        ctx = {
            'system_email': company_email,
            'requester_name': requester_name,
            'requester_email': requester_email,
            'notify_person_email': user.partner_id.email,
            'notify_person_name': user.partner_id.name,
            'url': the_url,
            'currency_code': self.env.user.company_id.currency_id.symbol,
        }
        # mail_template.with_context(ctx).send_mail(self.id, force_send=False)
        # self.env.user.notify_info('%s Will Be Notified by Email' % (user.name))

        return res


    @api.one
    
    def approve_expenses(self):
        if self.state != 'submit' :
            raise UserError('Sorry, you can only approve submitted expenses')
        if self.line_manager_id.user_id != self.env.user :
            raise UserError('Please contact %s to approve this record' % (self.line_manager_id.name))

        if not self.company :
            raise UserError('Please set the company for the expense line')
        else:
            company = self.env['res.company'].sudo().search([('company_select', '=', self.company)])
            journal_id = self.sudo().env['account.journal'].search([('type', '=', 'purchase'),('company_id', '=', company.id)], limit=1)
            self.write({'state': 'audit_approve','emp_expense_group_aud_id':company.auditor_group_id.id,'emp_expense_group_acc_id':company.accountant_group_id.id,'company_id':company.id,'journal_id':journal_id.id})



        if any(expense.state not in ('draft','submit') for expense in self.expense_group_id.expense_line_ids):
            self.expense_group_id.state = 'done'

        #  send email
        # user_ids = []
        # group_obj = self.env.ref('kkon_modifications.group_kkon_expense_auditor_kkon')
        # user_names = ''
        # for user in group_obj.sudo().users:
        #     user_names += user.name + ", "
        #     user_ids.append(user.partner_id.id)
        # if user_ids :
        #     self.message_post(
        #         _(
        #             'A New Expense (%s) has been approved by %s, and it requires the approval from the auditor') % (
        #             self.name, self.env.user.name),
        #         subject='A New Expense approved by line manager', partner_ids=[user_ids], subtype_xmlid='mail.mt_comment', force_send=False)
        #     self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
        ctx = {}
        ctx.update({'expense_group_id': self.sudo().expense_group_id.id})
        the_url = self._get_url('kkon_modifications', 'menu_hr_expense_group_kkon', 'action_hr_expense_group_kkon', ctx)
        mail_template = self.env.ref('kkon_modifications.mail_templ_approve_expense_kkon')

        company_email = self.env.user.company_id.email
        requester_email = self.expense_group_id.line_manager_id.user_id.partner_id.email
        requester_name = self.expense_group_id.line_manager_id.user_id.partner_id.name

        user_names = ''
        users = self.emp_expense_group_aud_id.sudo().user_ids
        for user in users:
            if user.is_group_email:
                user_names += user.name + ", "
                ctx = {
                    'system_email': company_email,
                    'requester_name': requester_name,
                    'requester_email': requester_email,
                    'notify_person_email': user.partner_id.email,
                    'notify_person_name': user.partner_id.name,
                    'url': the_url,
                    'currency_code': self.env.user.company_id.currency_id.symbol,
                }
        #         mail_template.with_context(ctx).send_mail(self.id, force_send=False)
        # self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))



    @api.one
    
    def audit_approve(self):
        if self.state != 'audit_approve' :
            raise UserError('Sorry, you can only approve audited expenses')
        if self.env.user not in self.emp_expense_group_aud_id.user_ids:
            raise UserError('Please contact any user in the  %s to approve this record' % (self.emp_expense_group_aud_id.name))

        self.state = 'approve'
        self.audited_by = self.env.user
        self.audited_date = datetime.today()

        # user_ids = []
        # group_obj = self.env.ref('account.group_account_user')
        # user_names = ''
        # for user in group_obj.sudo().users:
        #     if user.is_group_email:
        #         user_names += user.name + ", "
        #         user_ids.append(user.partner_id.id)
        # if user_ids:
        #     self.message_post(
        #         _(
        #             'A New Expense (%s), has been approved by the auditor - %s, and may now be posted to the GL') % (
        #             self.name, self.env.user.name),
        #         subject='A New Expense approved by the auditor', partner_ids=[user_ids], subtype_xmlid='mail.mt_comment', force_send=False)
        #     self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
        ctx = {}
        ctx.update({'expense_group_id': self.expense_group_id.id})
        the_url = self._get_url('kkon_modifications', 'menu_hr_expense_group_kkon', 'action_hr_expense_group_kkon', ctx)
        mail_template = self.env.ref('kkon_modifications.mail_templ_audit_approve_expense_kkon')

        company_email = self.env.user.company_id.email
        requester_email = self.audited_by.partner_id.email
        requester_name = self.audited_by.partner_id.name

        user_names = ''
        users = self.emp_expense_group_acc_id.sudo().user_ids
        for user in users:
            if user.is_group_email:
                user_names += user.name + ", "
                ctx = {
                    'system_email': company_email,
                    'requester_name': requester_name,
                    'requester_email': requester_email,
                    'notify_person_email': user.partner_id.email,
                    'notify_person_name': user.partner_id.name,
                    'url': the_url,
                    'currency_code': self.env.user.company_id.currency_id.symbol,
                }
        #         mail_template.with_context(ctx).send_mail(self.id, force_send=False)
        # self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

    
    def action_move_create(self):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        if any(expense.state != 'approve' for expense in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(expense.employee_id != self[0].employee_id for expense in self):
            raise UserError(_("Expenses must belong to the same Employee."))

        if any(not expense.journal_id for expense in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        journal_dict = {}
        maxdate = False
        for expense in self:
            if expense.date > maxdate:
                maxdate = expense.date
            if expense.journal_id not in journal_dict:
                journal_dict[expense.journal_id] = []
            journal_dict[expense.journal_id].append(expense)

        for journal, expense_list in journal_dict.items():
            # create the move that will contain the accounting entries
            move = self.env['account.move'].create({
                'journal_id': journal.id,
                'company_id': self.env.user.company_id.id,
                'date': maxdate,
            })
            for expense in expense_list:
                company_currency = expense.company_id.currency_id
                diff_currency_p = expense.currency_id != company_currency
                # one account.move.line per expense (+taxes..)
                move_lines = expense._move_line_get()

                # create one more move line, a counterline for the total on payable account
                total, total_currency, move_lines = expense._compute_expense_totals(company_currency, move_lines,
                                                                                    maxdate)
                if expense.payment_mode == 'company_account':
                    if not expense.bank_journal_id.default_credit_account_id:
                        raise UserError(_("No credit account found for the %s journal, please configure one.") % (
                            expense.bank_journal_id.name))
                    emp_account = expense.bank_journal_id.default_credit_account_id.id
                else:
                    if not expense.employee_id.address_home_id:
                        raise UserError(_("No Home Address found for the employee %s, please configure one.") % (
                            expense.employee_id.name))
                    emp_account = expense.employee_id.address_home_id.property_account_payable_id.id

                move_lines.append({
                    'type': 'dest',
                    'name': expense.employee_id.name,
                    'price': total,
                    'account_id': emp_account,
                    'date_maturity': expense.date,
                    'amount_currency': diff_currency_p and total_currency or False,
                    'currency_id': diff_currency_p and expense.currency_id.id or False,
                    'ref': expense.employee_id.address_home_id.ref + ' ' + expense.expense_ref or False
                })

                # convert eml into an osv-valid format
                lines = map(lambda x: (0, 0, expense._prepare_move_line(x)), move_lines)
                move.write({'line_ids': lines})
                expense.write({'account_move_id': move.id, 'state': 'post'})
                if expense.payment_mode == 'company_account':
                    expense.paid_expenses()
            move.post()
        return True

    @api.one
    
    def action_move_create(self):
        if self.env.user not in self.emp_expense_group_acc_id.user_ids:
            raise UserError('Please contact any user in the  %s to post this record' % (self.emp_expense_group_acc_id.name))
        if not self.product_id :
            raise UserError('Please Select an Expense Type before posting this record')

        date_container = self.date
        if self.posted_date :
            self.date = self.posted_date
        else:
            self.date = datetime.today()
        res = super(HRExpense,self).action_move_create()
        self.posted_by = self.env.user
        self.date = date_container # set back the expense group date

        ctx = {}
        ctx.update({'expense_group_id': self.expense_group_id.id})
        the_url = self._get_url('kkon_modifications', 'menu_hr_expense_group_kkon', 'action_hr_expense_group_kkon', ctx)
        mail_template = self.env.ref('kkon_modifications.mail_templ_post_expense_kkon')

        company_email = self.env.user.company_id.email
        requester_email = self.posted_by.partner_id.email
        requester_name = self.posted_by.partner_id.name

        user_names = ''
        users = self.emp_expense_group_acc_id.user_ids
        for user in users:
            if user.is_group_email:
                user_names += user.name + ", "
                ctx = {
                    'system_email': company_email,
                    'requester_name': requester_name,
                    'requester_email': requester_email,
                    'notify_person_email': user.partner_id.email,
                    'notify_person_name': user.partner_id.name,
                    'url': the_url,
                    'currency_code': self.env.user.company_id.currency_id.symbol,
                }
        #         mail_template.with_context(ctx).send_mail(self.id, force_send=False)
        # self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
        return res


    
    def unlink(self):
        for rec in self:
            if rec.expense_group_id.employee_id.user_id != rec.env.user:
                raise UserError('Sorry, only %s  cannot delete an existing expense in this expense group' % (rec.expense_group_id.employee_id.name))
        return super(HRExpense, self).unlink(self)

    
    def create(self, vals):
        res = super(HRExpense, self).create(vals)
        if res.expense_group_id.employee_id.user_id !=  self.env.user:
            raise UserError('Sorry, only %s  can create a new expense in this expense group' % (res.expense_group_id.employee_id.name))

        if res.expense_group_id.state == 'done':
            raise UserError('Sorry, you cannot add a new expense line on a done expense group, please create a new expense group.')
        return res

    
    def write(self, vals):
        for rec in self:
            employee = rec.employee_id
            if not employee.parent_id :
                raise UserError(_('Please Contact the Admin or HR Officer to Set the Manager for the Employee - %s' % (employee.name)))
            if not employee.parent_id.user_id:
                raise UserError(_('Please Contact the Admin or HR officer to Set the User for the Manager - %s' % (employee.parent_id.name)))

            company = vals.get('company',False)
            if company and self.env.user != rec.line_manager_id.user_id :
                raise UserError('Only the Line Manager (%s) is allowed to change the company field' % (self.line_manager_id.name))

            vals['department_manager_id'] = employee.parent_id.user_id.id
            res = super(HRExpense, rec).write(vals)
            return res

    # @api.onchange('company_id')
    # def _onchange_company_id(self):
    #     company = self.company_id
    #     if company:
    #         self.emp_expense_group_aud_id = company.auditor_group_id
    #         self.emp_expense_group_acc_id = company.accountant_group_id
    #

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.name:
                self.name = self.product_id.display_name or ''
            self.product_uom_id = self.product_id.uom_id
            self.tax_ids = self.product_id.supplier_taxes_id

    state = fields.Selection([('draft', 'To Submit'),
                             ('submit', 'Submitted'),
                             ('approve', 'Awaiting Account Posting'),
                              ('audit_approve', 'Awaiting Audit Approval'),
                             ('post', 'Awaiting Payment'),
                             ('done', 'Paid'),
                             ('cancel', 'Refused')
                             ], string='Status', index=True, readonly=True, tracking=True, copy=False,
                            default='draft', required=True,
                            help='When the expense request is created the status is \'To Submit\'.\n It is submitted by the employee and request is sent to manager, the status is \'Submitted\'.\
            \nIf the manager approve it, the status is \'Approved\'.\n If the accountant genrate the accounting entries for the expense request, the status is \'Waiting Payment\'.')
    department_manager_id = fields.Many2one('res.users',string='Department Manager')
    product_id = fields.Many2one('product.product', string='Expense Type', readonly=True, states={'draft': [('readonly', True),('required', False)],'submit': [('readonly', True),('required', False)],'approve': [('readonly', False),('required', False)],'audit_approve': [('readonly', True),('required', False)],'post': [('readonly', True),('required', False)]}, domain=[('can_be_expensed', '=', True)],required=False)
    company_id = fields.Many2one('res.company', string='Company', readonly=True,  states={'draft': [('readonly', False)],'submit': [('readonly', False)]}, default=False)
    expense_type_id = fields.Many2one('kkon.expense.type',string='Expense Type')
    exp_group_count = fields.Integer(compute="_compute_exp_group_count", string='# of Expense Groups', copy=False, default=0)
    expense_group_id = fields.Many2one('hr.expense.group.kkon',string='Expense Group')
    employee_id = fields.Many2one('hr.employee',related='expense_group_id.employee_id',string='Employee',store=True)
    date = fields.Date(string='Date',related='expense_group_id.date',store=True)
    line_manager_id = fields.Many2one('hr.employee', related='expense_group_id.line_manager_id', string='Line Manager', store=True)
    emp_expense_group_aud_id = fields.Many2one('emp.expense.group', string='Employee Expense Auditor Group', ondelete='restrict')
    emp_expense_group_acc_id = fields.Many2one('emp.expense.group', string='Employee Expense Accountant Group', ondelete='restrict')
    refused_msg = fields.Text(string='Refused Reason')
    refused_by = fields.Many2one('res.users', string='Refused By')
    refused_date = fields.Datetime(string='Refused DateTime')
    audited_by = fields.Many2one('res.users', string='Audited By')
    audited_date = fields.Datetime(string='Audited DateTime')
    posted_by = fields.Many2one('res.users', string='Posted By')
    posted_date = fields.Datetime(string='Posted DateTime')
    paid_by = fields.Many2one('res.users', string='Paid By')
    paid_date = fields.Datetime(string='Paid DateTime')
    company = fields.Selection([('kkon', 'KKONTech'),
                              ('fob', 'FOB')
                              ], string='Company', readonly=True,  states={'draft': [('readonly', False)],'submit': [('readonly', False)]}, default=False)
    payment_mode = fields.Selection(default='company_account')
    bank_journal_id = fields.Many2one(default=False)
    expense_ref = fields.Char(string='Expense Ref.')

class HRExpenseGroup(models.Model):
    _name = 'hr.expense.group.kkon'
    _inherit = ['mail.thread']
    _order = 'expid desc'


    
    def btn_done(self):
        if not self.expense_line_ids:
            raise UserError('Please enter at least one expense line')
        self.state = 'done'

    
    def btn_reset(self):
        self.state = 'draft'



    # 
    # def unlink(self):
    #     for rec in self:
    #         if rec.state not in ['draft']:
    #             raise UserError(_('You can only delete draft Expense Group'))

    
    def create(self, vals):
        vals['expid'] = self.env['ir.sequence'].next_by_code('exp_group_id_code') or 'New'
        res = super(HRExpenseGroup, self).create(vals)
        return res

    
    def _get_employee(self):
        return self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)

    
    def _get_department(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        return employee.department_id

    
    def _get_manager(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        return employee.parent_id

    
    def _get_general_hr_expense_group(self):
        return self.env['emp.expense.group'].search([('is_general', '=', True)], limit=1)



    @api.depends('expense_line_ids.total_amount')
    def _amount_all(self):
        for rec in self:
            total_amount  = 0.0
            for line in rec.expense_line_ids:
                total_amount += line.total_amount
                rec.update({
                'amount_total' : rec.currency_id.round(total_amount),
            })

    name = fields.Char(string='Title')
    expid = fields.Char(string='Expense ID')
    employee_id = fields.Many2one('hr.employee',string='Employee',default=_get_employee)
    user_id = fields.Many2one('res.users',string='User', default=lambda self: self.env.user)
    department_id = fields.Many2one('hr.department',string='Department',default=_get_department)
    line_manager_id = fields.Many2one('hr.employee', string='Line Manager', default=_get_manager)
    date = fields.Date(string='Date',default=lambda self: datetime.today())
    expense_line_ids = fields.One2many('hr.expense','expense_group_id',string='Expense Lines')
    amount_total = fields.Monetary(string='Total', store=True, compute='_amount_all',
                                   track_visibility='always')
    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id, ondelete='restrict')
    emp_expense_group_general_id = fields.Many2one('emp.expense.group', default=_get_general_hr_expense_group, string='Employee Expense General Group', ondelete='restrict')
    state = fields.Selection([('draft', 'New'),
                              ('done', 'Manager Done')
                              ], string='Status', default='draft')



class ResUser(models.Model):
    _inherit = 'res.users'

    emp_expense_group_ids = fields.Many2many('emp.expense.group', 'emp_expense_group_rel', 'user_id','emp_expense_group_id', string='Employee Expense Groups', ondelete='restrict')


class EmployeeExpenseGroup(models.Model):
    _name = 'emp.expense.group'

    
    def create(self, vals):
        self.clear_caches()
        return super(EmployeeExpenseGroup,self).create(vals)

    # Clear cache for Record Rules to take effect without restarting the server, for many2many fields. It does not apply to other type of fields
    
    def write(self, vals):
        # Record rules based on many2many relationship were not applied when many2many fields values were modified.
        # Record rules based on many2many relationship were not applied when many2many fields values were modified.
        #This not affect unlink/deletion of records, so no need to clear cache for unlink()
        self.clear_caches()  # ref: https://www.odoo.com/forum/help-1/question/force-odoo-to-delete-cache-81650
        return super(EmployeeExpenseGroup,self).write(vals)

    name = fields.Char(string='Employee Expense Group')
    user_ids =  fields.Many2many('res.users', 'emp_expense_group_rel', 'emp_expense_group_id', 'user_id', string='Employees', ondelete='restrict')
    company_id = fields.Many2one('res.company',string='Company')
    is_general = fields.Boolean(string='Is General Group',help="For allowing other users that should see the Expense Group Model")


class ResCompany(models.Model):
    _inherit = "res.company"

    auditor_group_id = fields.Many2one('emp.expense.group', string='Auditor Group')
    accountant_group_id = fields.Many2one('emp.expense.group', string='Accountant Group')

