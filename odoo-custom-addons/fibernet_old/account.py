# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017-2020  Kinsolve Solutions
# Copyright 2017 -2020 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from datetime import datetime,date, timedelta
from odoo import api, fields, models, _
from urllib import urlencode
from urlparse import urljoin
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare,float_round, DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    
    def action_invoice_sent_kkon(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('kkon_modifications.email_template_edi_invoice_kkon', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.invoice',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    
    def action_invoice_sent_fob(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('kkon_modifications.email_template_edi_invoice_fob', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.invoice',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    is_eservice_invoice = fields.Boolean(string='Is Eservice Invoice')
    payment_group_id = fields.Many2one('account.payment.group',string='Eservice Payment')
    is_upcountry = fields.Boolean(string='Up Country Transaction')




class AccountPaymentGroup(models.Model):
    _inherit = 'account.payment.group'

    
    def unlink(self):
        for rec in self:
            if rec.is_from_eservice :
                raise UserError('Sorry, Eservice Payment Cannot be deleted')
        return super(AccountPaymentGroup,self).unlink()


    def send_receipt(self):
        company_email = self.env.user.company_id.email.strip()
        sender_person_email = self.env.user.partner_id.email.strip()
        customer_email = self.partner_id.email and self.partner_id.email.strip() or False

        if company_email and sender_person_email and customer_email:
            mail_template = self.env.ref('kkon_modifications.email_template_payment_receipt_ebilling')

            if self.company_id.company_select == 'fob':
                mail_template.email_from = 'newsales@fob.ng'
                mail_template.email_cc = 'invoice@fob.ng'
                #mail_template.subject = 'FiberOne Broadband Payment Receipt'
            mail_template.send_mail(self.id, force_send=False)
            self.is_sent_receipt_eservice = True
        return


    def create_customer_invoice(self, date, amount, ref, partner_id, prd_id,company_id):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))

        invoice_vals = {
            'date_invoice' : date,
            'name': ref or '',
            'type': 'out_invoice',
            'reference': ref or '',
            'account_id': self.env['res.partner'].browse(partner_id).property_account_receivable_id.id,
            'partner_id': partner_id,
            'journal_id': journal_id,
            'is_eservice_invoice': True,
            'user_id': self.env.uid,
            'team_id' : False,
            'company_id': company_id,
        }
        invoice = inv_obj.create(invoice_vals)


        product_tmpl_id = self.env['product.template'].browse(prd_id)
        product_id = product_tmpl_id.product_variant_ids[0]
        if not product_id:
            raise UserError('There is No Product for the Product Template')
        if not float_is_zero(1, precision_digits=precision):
            account = product_id.property_account_income_id or product_id.categ_id.property_account_income_categ_id
            if not account:
                raise UserError(
                    _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % (
                    product_id.name, product_id.id,
                    product_id.categ_id.name))

            inv_line = {
                'name': ref or '',
                # 'sequence': self.sequence,
                'origin': ref or '',
                'account_id': account.id,
                'price_unit': amount,
                'quantity': 1,
                'uom_id': product_id.uom_id.id,
                'product_id': product_id.id or False,
                'invoice_id': invoice.id,
                'invoice_line_tax_ids': [(6, 0, [2])],
                'company_id': company_id,
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
        invoice.signal_workflow('invoice_open')
        return invoice


    
    def action_create_payment(self,payment_date,journal_id,amount,ref,partner_id,company_id):
        account_payment_group_obj = self.env['account.payment.group']
        account_payment_obj = self.env['account.payment']

        act_pg_dict = {
            'partner_id': partner_id,
            'payment_date': payment_date,
            'communication': ref,
            'partner_type': 'customer',
            'is_from_eservice' : True,
            'company_id': company_id,
        }
        res = account_payment_group_obj.create(act_pg_dict)
        res._refresh_payments_and_move_lines()
        acc_pay = {
            'payment_type': 'inbound',
            'payment_type_copy': 'inbound',
            'journal_id': journal_id,
            'payment_date': payment_date,
            'amount': amount,
            'communication': ref,
            'ref_no': ref,
            'payment_method_id': 1,  # Manual payment
            'partner_id': partner_id,
            'partner_type': 'customer',
            'payment_group_id': res.id,
            'company_id': company_id,
        }
        pg = account_payment_obj.create(acc_pay)
        res.post()
        return res

    
    def create(self, vals):
        res = False
        if 'is_from_rpc' in vals:
            date = vals.get('date',False)
            journal_id = vals.get('journal_id', False)
            amount = vals.get('amount', 0)
            num_renewal = vals.get('num_renewal', 0)
            if num_renewal == 0:
                raise UserError('Number of renewal is not present. Please set it and repush')
            ref = vals.get('ref', '')
            partner_id = vals.get('partner_id', False)
            prd_id = vals.get('product_id',False)
            company_id = vals.get('company_id',False)
            if not company_id:
                raise UserError('Company ID is required')

            i = 0
            while i < num_renewal:
                the_date = datetime.strptime(date, '%Y-%m-%d')
                new_date = the_date + relativedelta(days=+i)
                tdate = new_date.strftime('%Y-%m-%d')
                inv = self.create_customer_invoice(tdate, (amount / num_renewal), ref, partner_id,prd_id,company_id)
                i += 30
            res = self.action_create_payment(date, journal_id, amount, ref, partner_id,company_id)
            #res.send_receipt()  #pause for now to debug the mutiple emails sent
            #res.eservice_invoice_id = inv
            #inv.payment_group_id = res
        else:
            res = super(AccountPaymentGroup, self).create(vals)
        return res

    is_from_eservice = fields.Boolean(string='Is From Eservice')
    eservice_invoice_id = fields.Many2one('account.invoice',string='Eservice Invoice')
    is_sent_receipt_eservice = fields.Boolean(string='Is Sent Receipt from Eservice')
    is_upcountry = fields.Boolean(string='Up Country Transaction')
