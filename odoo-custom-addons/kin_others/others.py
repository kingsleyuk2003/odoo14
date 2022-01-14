# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017-2021  Kinsolve Solutions
# Copyright 2017-2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from odoo import api, fields, models, _
from datetime import datetime, timedelta


class CompanyExtend(models.Model):
    _inherit = 'res.company'

    @api.model
    def run_retry_sending_failed_email(self):
        mail_obj = self.env['mail.mail']

        mails = mail_obj.search([('state','=','exception'),('failure_reason','ilike', 'Mail delivery failed via SMTP server')])

        #retry sending the email
        for mail in mails :
            mail.mark_outgoing()
            mail.send()


        #Send Email
        if len(mails) > 0 :
            company_email = self.env.user.company_id.email.strip()
            company_name = self.env.user.company_id.name
            if company_email :
                users = self.env['res.users'].search([('active','=',True),('company_id', '=', self.env.user.company_id.id)])

                msg = ''
                the_date = datetime.today().strftime('%d-%m-%Y')
                msg += "<p>Hello Admin,</p>"
                msg += "<p>Mail Delivery Failed for the Company - %s on %s. An Attempt has been made to resend the failed email, but you may still check the email queue for other messaging issues.</p><p></p>"  % (company_name,the_date)
                msg += "Regards and Thanks"
                for user in users :
                    if user.has_group('kin_others.group_mail_delivery_failed') and user.partner_id.email and user.partner_id.email.strip() :
                        #Send Email
                        mail_data = {
                            'model': 'mail.mail',
                            'res_id': self.id,
                            'record_name': 'Mail Delivery Failed',
                            'email_from': company_email,
                            'reply_to': company_email,
                            'subject': "Mail Delivery Failed from %s" % (company_name),
                            'body_html': '%s' % msg,
                            'auto_delete': True,
                            #'recipient_ids': [(4, id) for id in new_follower_ids]
                            'email_to': user.partner_id.email
                        }
                        mail_id = mail_obj.create(mail_data)
                        mail_obj.send([mail_id])
            return True


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_group_email = fields.Boolean(string='Is Group Email')
    img_signature = fields.Binary(string='Signature Image')