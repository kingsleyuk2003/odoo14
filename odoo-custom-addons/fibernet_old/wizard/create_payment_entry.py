# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class CreatePaymentEntry(models.TransientModel):
    _name = 'create.payment.wizard'
    _description = 'Create Payment Wizard'


    
    def action_create_payment(self):
        rec = self.env.context['active_id']
        sale_order = self.env['sale.order'].browse(rec)
        is_free_paid_installation = self.is_free_paid_installation
        if is_free_paid_installation == 'paid' :
            res = sale_order.action_create_payment(self.payment_date,self.journal_id,self.amount,self.ref,self.partner_id)
            if res.is_upcountry :
                res.is_upcountry = True

            #check if the payment is complete
            if sale_order.amount_total != sale_order.total_amount_paid:
                currency_symbol = self.currency_id.symbol
                sale_order.alert_msg = 'Sales Order Price (%s %s) does not Match Total Payment Received (%s %s). Balance to be paid is (%s %s). This sales order will be finally approved when balance payment is accurately paid' % (currency_symbol,sale_order.amount_total,currency_symbol,sale_order.total_amount_paid,currency_symbol,sale_order.amount_balance)

            if sale_order.amount_total == sale_order.total_amount_paid:
                sale_order.create_ticket_with_email()
                # notify ebilling that this order has been approved
                if sale_order.ebilling_order_push and not sale_order.ebilling_order_manually_approved_pushed:
                    sale_order.ebilling_push_sale_order_approved()
                    sale_order.ebilling_order_manually_approved_pushed = True

                user_names = ''
                # Send Email to Sales person
                sale_user_id = sale_order.user_id
                if not sale_user_id:
                    raise UserError('Please set the Sales Person for the sales order')
                else:
                    msg = '%s payment receipt has been posted by %s for the sales order with id %s' % (
                        sale_order.partner_id.name, sale_order.env.user.name, sale_order.name)
                    sale_order.message_post(msg, subject='%s' % msg, partner_ids=[sale_user_id.partner_id.id])
                    user_names += sale_user_id.name + ", "
                sale_order.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

                if self.is_send_receipt :
                    return res.action_receipt_sent()
        elif is_free_paid_installation == 'free' :
            if sale_order.amount_balance != 0 :
                raise UserError('Sorry, you cannot register a free installation payment for this sales order, since some initial payment(s) have been received. You can rather cancel this order and re-approve to register a free installtion payment ')
            sale_order.is_free_installation = True
            sale_order.create_ticket_with_email()
        else:
            raise UserError('Please indicate if the installation is free or paid')

        return

    is_free_paid_installation = fields.Selection([('paid', 'Paid Installation'),('free', 'Free Installation')
                              ], string='Free or Paid Installation')
    payment_date = fields.Date(string='Payment Date')
    journal_id = fields.Many2one('account.journal',string='Payment Method')
    amount = fields.Float(string='Amount Paid')
    ref = fields.Char(string='Note')
    is_send_receipt = fields.Boolean(string="Send Receipt to Customer")
    partner_id = fields.Many2one('res.partner',string='Customer')
    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    total_amount_paid = fields.Monetary(string='Total Amount Paid')
    amount_balance = fields.Monetary(string='Balance to be Paid')

