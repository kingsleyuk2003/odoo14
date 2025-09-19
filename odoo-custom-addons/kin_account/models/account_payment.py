# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime,date, timedelta
from odoo.exceptions import UserError, ValidationError
# import base64
# from odoo.tools.misc import format_amount

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def amount_to_text(self, amt):
        amount_text = self.currency_id.amount_to_text(amt)
        return str.upper('**** ' + amount_text + '**** ONLY')

    # def action_receipt_plain_sent_no_logging_no_button_document(self):
    #     #this is just raw email without the default sent by footer, view button and there is no email log on the document
    #     report = self.env.ref('kin_account.action_report_receipt')._render_qweb_pdf(self.id)
    #
    #     name = '%s Payment Recieipt (%s)' % (self.env.company.name, self.name)
    #     filename = name + '.pdf'
    #     receipt = self.env['ir.attachment'].create({
    #         'name': filename,
    #         'type': 'binary',
    #         'datas': base64.b64encode(report[0]),
    #         'store_fname': filename,
    #         'res_model': 'account.payment',
    #         'res_id': self.id,
    #         # 'mimetype': 'application/x-pdf'
    #     })
    #     mail_values = {
    #         'subject': name,
    #         'body_html': 'test email',
    #         'author_id': self.env.user.partner_id.id,
    #         'email_from': self.env.company.email or self.env.user.email_formatted,
    #         'email_to': self.partner_id.email,
    #         'attachment_ids': [(4, receipt.id)],
    #         'auto_delete': True
    #     }
    #     mail_values['attachment_ids'] += [(4, receipt.id)]
    #     mail = self.env['mail.mail'].sudo().create(mail_values)
    #     #mail.send()
    #     mail.mark_outgoing()



    def action_receipt_sent(self):
        self.ensure_one()
        template = self.env.ref('kin_account.email_template_payment_receipt', False)
        lang = self.env.context.get('lang')
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]

        ctx = {
            'default_model': 'account.payment',
            'default_res_id': self.id,
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'mark_receipt_as_sent': True,
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
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

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_receipt_as_sent'):
            self.filtered(lambda o: o.state == 'draft').with_context(tracking_disable=True).write({'state': 'sent'})
        return super(AccountPayment, self.with_context(mail_post_autofollow=False)).message_post(**kwargs)

    @api.constrains('date')
    def check_date(self):
        for rec in self:
            set_date = rec.date
            restrict_users = self.env.ref('kin_account.group_restrict_account_date').users
            restrict_back_date = self.env['ir.config_parameter'].sudo().get_param('kin_account.restrict_back_date', default=False)
            restrict_days = self.env['ir.config_parameter'].sudo().get_param('kin_account.restrict_days', default=0)
            if set_date and self.env.user in restrict_users and restrict_back_date:
                dayback = restrict_days
                selected_date = datetime.strptime(set_date, "%Y-%m-%d")
                allowed_date = datetime.strptime(str(date.today()), "%Y-%m-%d") - timedelta(days=+dayback)
                if selected_date < allowed_date:
                    raise ValidationError(
                        'Backdating is not allowed, before %s ' % (datetime.strftime(allowed_date, '%d-%m-%Y')))


    def action_post(self):
        res = super(AccountPayment,self).action_post()
        for rec in self:
            rec.move_id.payment_id = rec
        return res


    def send_grp_email(self, grp_name, subject, msg):
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref(grp_name)
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)
        if partn_ids:
            # self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partn_ids, subtype_xmlid='mail.mt_comment',
                              force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

    def action_draft(self):
        self.is_request_approval_sent = False
        self.is_request_approval_by = False
        self.is_request_approval_date = False
        return super(AccountPayment, self).action_draft()

    def btn_request_approval(self):
        if self.state == 'posted':
            raise UserError('Sorry, the record has already been posted')
        if self.state == 'cancel':
            raise UserError('Sorry, the record is cancelled')
        msg = 'Payment Entry (%s) from %s requires your approval' % (self.name, self.env.user.name)
        self.send_grp_email(grp_name='kin_account.group_account_payment_receive_request_approval_email', subject=msg, msg=msg)
        self.is_request_approval_sent = True
        self.is_request_approval_by = self.env.user
        self.is_request_approval_date = fields.Datetime.now()

    @api.onchange('partner_id_customer')
    def _compute_partner_id_customer(self):
        for rec in self:
            rec.partner_id = rec.partner_id_customer

    @api.onchange('partner_id_supplier')
    def _compute_partner_id_supplier(self):
        for rec in self:
            rec.partner_id = rec.partner_id_supplier


    is_request_approval_sent = fields.Boolean(string='Is Request Approval Sent', copy=False, tracking=True)
    is_request_approval_by = fields.Many2one('res.users', string='Requested By', copy=False, tracking=True)
    is_request_approval_date = fields.Datetime(string='Request Approval Date', copy=False, tracking=True)
    partner_id_customer = fields.Many2one(related='partner_id', readonly=False,  check_company=True,string="Customer")
    partner_id_supplier = fields.Many2one(related='partner_id', readonly=False,  check_company=True,string="Vendor")

