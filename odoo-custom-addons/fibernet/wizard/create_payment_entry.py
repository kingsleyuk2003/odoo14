# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class CreatePaymentEntry(models.TransientModel):
    _name = 'create.payment.wizard'
    _description = 'Create Payment Wizard'


    def action_create_payment(self):
        rec = self.env.context['active_id']
        sale_order = self.env['sale.order'].browse(rec)
        is_paid_deferred = self.is_paid_deferred
        if is_paid_deferred == 'paid' :
            res = sale_order.action_create_payment(self.payment_date,self.journal_id,self.amount,self.ref,self.partner_id)

            #check if the payment is complete
            if sale_order.amount_total != sale_order.total_amount_paid:
                currency_symbol = self.currency_id.symbol
                sale_order.alert_msg = 'Total Sales Amount (%s %s) does not Match Total Payment Received (%s %s). Balance to be paid is (%s %s). This sales order will be finally approved when balance payment is completely paid' % (currency_symbol,sale_order.amount_total,currency_symbol,sale_order.total_amount_paid,currency_symbol,sale_order.amount_balance)

            if sale_order.amount_total == sale_order.total_amount_paid:
                sale_order.create_ticket_with_email()
            elif sale_order.total_amount_paid > sale_order.amount_total :
                raise UserError('Total Amount paid is greater than Sales Amount')
            elif sale_order.total_amount_paid <= 0 :
                raise UserError('Amount paid is less than or equal to Zero ')

            sale_order.send_email_to_sales_person()
            if self.is_send_receipt :
                return res.action_receipt_plain_sent_no_logging_no_button_document()
        elif is_paid_deferred == 'deferred' :
            if sale_order.amount_balance != 0 :
                raise UserError('Sorry, you cannot register a deferred installation payment for this sales order, since some initial payment(s) have been received. You can rather cancel this order and re-approve to register a deferred payment ')
            sale_order.is_deferred_payment = True
            sale_order.create_ticket_with_email()
        else:
            raise UserError('Please indicate if the payment is deferred or paid')



        return True

    is_paid_deferred = fields.Selection([('paid', 'Paid'),('deferred', 'Deferred')], string='Paid or Deferred Payment')
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
