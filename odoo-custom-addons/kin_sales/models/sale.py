# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import *
from dateutil.relativedelta import relativedelta

class CrmTeamExtend(models.Model):
    _inherit = 'crm.team'

    warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse')
    sale_stock_location_ids = fields.Many2many('stock.location',string="Sale Stock Locations",help="stock locations where sold items are to delivered from")

    @api.model
    def _get_default_team_id(self, user_id=None, domain=None):
        res = None
        is_select_sales_team = self.env['ir.config_parameter'].sudo().get_param(
            'is_select_sales_team', default=False)
        if not is_select_sales_team :
            res = super(CrmTeamExtend,self)._get_default_team_id(user_id=user_id , domain=None)
        return res


class SaleOrderExtend(models.Model):
    _inherit = "sale.order"

    # def _prepare_confirmation_values(self):
    #     return {
    #         'state': 'sale'
    #     }



    def send_grp_email(self, grp_name, subject, msg):
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref(grp_name)
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)
        if partn_ids:
            #self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

    def action_draft(self):
        self.is_request_approval_sent = False
        self.is_request_approval_by = False
        self.is_request_approval_date = False
        return super(SaleOrderExtend, self).action_draft()


    def btn_request_approval(self):
        if self.state == 'done' :
            raise UserError('Sorry, the record has already been approved')
        if self.state == 'cancel' :
            raise UserError('Sorry, the record is cancelled')
        msg = 'Sales Order (%s) from %s requires your approval' % (self.name,self.env.user.name)
        self.send_grp_email(grp_name='kin_sales.group_sales_order_receive_request_approval_email',subject=msg, msg=msg)
        self.is_request_approval_sent = True
        self.is_request_approval_by = self.env.user
        self.is_request_approval_date = fields.Datetime.now()


    def send_email(self, grp_name, subject, msg):
        partn_ids = []
        user_names = ''
        group_obj = self.env.ref(grp_name)
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)
        if partn_ids:
            #self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
            self.message_follower_ids.unlink()
            self.message_post(body=msg, subject=subject, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

    def reminder_validity_date(self):
        today = date.today()
        validity_date_interval = self.env['ir.config_parameter'].sudo().get_param('validity_date_interval', default=False)
        orders = self.search([('validity_date', '>=', today),('state', 'in', ('draft', 'sent', 'quote_submitted', 'so_to_approve'))])

        for order in orders:
            remaining_days = (order.validity_date - date.today()).days
            if remaining_days <= int(validity_date_interval):
                #send reminder email to sales person
                partn_ids = []
                user = order.user_id
                partn_ids.append(user.partner_id.id)

                if partn_ids:
                    order.message_follower_ids.unlink()
                    msg = "Sales Quotation (%s) Expiration Reminder in %s days" % (order.name,remaining_days)
                    subject = 'This is to notify you of the Sales Order (%s) that is about to expire in %s days time for %s' % (order.name, remaining_days, order.partner_id.name),
                    order.message_post(
                        body=msg,
                        subject=subject, partner_ids=partn_ids,
                        subtype_xmlid='mail.mt_comment', force_send=False)

                # send email to group
                group_name = 'kin_sales.group_receive_expiry_reminder_sale_order_email'
                order.send_email(group_name, subject, msg)
        return

    @api.model
    def run_sales_order_expiration_check(self):
        is_send_expiry_reminder_email_quote_notification = self.env['ir.config_parameter'].sudo().get_param('is_send_expiry_reminder_email_quote_notification',False)
        if is_send_expiry_reminder_email_quote_notification:
            self.reminder_validity_date()

        #for expired sales quotations
        today = date.today()
        orders = self.search(
            [('validity_date', '<', today), ('state', 'in', ('draft', 'sent'))])

        for order in orders:
            # send email
            order.send_email(grp_name='kin_sales.group_receive_sale_order_expiration_email',
                             subject='Expiration Notification for Sales Order (%s)' % order.name,
                             msg='The Sales Order/Quotation (%s) with expiration date (%s) has expired.' % (
                                 order.name, order.validity_date.strftime('%d-%m-%Y')))

            is_delete_quote_after_expiration_date = self.env['ir.config_parameter'].sudo().get_param(
                'is_delete_quote_after_expiration_date', False)
            if is_delete_quote_after_expiration_date:
                order.action_cancel()
                order.action_draft()
                order.unlink()

        return True



    def get_low_stock_msg(self):
        sale_order = self
        stock_locations = ""
        sale_team = sale_order.team_id
        sale_stock_loc_ids = sale_team.sale_stock_location_ids
        list_data = sale_order.check_sales_product_available_qty(sale_stock_loc_ids)
        msg = ""
        stock_locations = ""
        if len(list_data) > 0:
            for stock_location in sale_stock_loc_ids:
                stock_locations += stock_location.name + ", "
            stock_locations = stock_locations.rstrip(', ')
            msg = ""
            sale_msg = ""
            sale_msg += "The following Items are lesser than the quantity available in the stock locations (%s) \n" % (
                stock_locations)
            count = 0
            for data_dict in list_data:
                for key, value in data_dict.items():  # keys = data_dict.keys()  # see ref: http://stackoverflow.com/questions/5904969/python-how-to-print-a-dictionarys-key
                    msg += "%s (%s) qty. is lesser than the quantity available in the stock locations (%s) \n" % (
                        key, value, stock_locations)
                    count += 1
                    sale_msg = "%s). %s (%s) qty. \n" % (count, key, value)
            msg += "Please contact the purchase manager to purchase the item(s) \n"
        return msg, stock_locations


    def create_advance_invoice(self):
        is_post_invoice_before_delivery = self.env['ir.config_parameter'].sudo().get_param(
            'is_post_invoice_before_delivery', default=False)

        # set the qty to invoice so that the invoice before delivery can be automated
        self.state = 'sale'
        for order_line in self.order_line:
            order_line._get_to_invoice_qty()

        # create advance invoice
        inv = self._create_invoices(final=True)
        inv.sale_ids = self
        inv.sale_order_id = self
        if is_post_invoice_before_delivery:
            inv.action_post()
        return



    def action_confirm(self):
        is_contraint_sales_order_stock = self.env['ir.config_parameter'].sudo().get_param(
            'is_contraint_sales_order_stock', default=False)
        is_sales_order_stock_notification = self.env['ir.config_parameter'].sudo().get_param(
            'is_sales_order_stock_notification', default=False)
        is_sales_order_stock_count_error = self.env['ir.config_parameter'].sudo().get_param(
            'is_sales_order_stock_count_error', default=False)
        is_sales_order_stock_purchase_request = self.env['ir.config_parameter'].sudo().get_param(
            'is_sales_order_stock_purchase_request', default=False)
        is_po_check = self.env['ir.config_parameter'].sudo().get_param('is_po_check', default=False)
        is_error_quote_after_expiration_date = self.env['ir.config_parameter'].sudo().get_param(
            'is_error_quote_after_expiration_date', default=False)

        if is_error_quote_after_expiration_date:
            # check if the order has expired
            if self.validity_date < date.today():
                raise UserError('This Sales Order has Expired')

        # is PO Check
        if is_po_check:
            if self.client_order_ref:
                client_order_ref = self.client_order_ref.strip()

                if len(client_order_ref) <= 0:
                    raise UserError(
                        'Please Ensure that the Quote is confirmed from the customer and that the PO reference is set. e.g. you may put the po number, email, contact name, number of the customer that confirmed the Quote on the PO reference field')

            else:
                raise UserError(
                    'Please Ensure that the Quote is confirmed from the customer and that the PO reference is set. e.g. you may put the po number, email, contact name, number of the customer that confirmed the Quote')


        # Low stock check
        msg, stock_locations = self.get_low_stock_msg()
        if msg and is_contraint_sales_order_stock and is_sales_order_stock_notification:
            # Check product qty if is less than 0 for each location
            sale_stock_loc_ids = self.team_id.sale_stock_location_ids

            # Create Purchase Request with email notification for low stock
            if is_sales_order_stock_purchase_request:
                pr_id = self.create_purchase_request(sale_stock_loc_ids)
                self.send_email(grp_name='kin_sales.group_receive_sale_order_purchase_request_email',
                                subject='Purchase Request from Sales Order (%s)' % self.name,
                                msg='A new purchase request document for the sales order (%s) has been created.' % self.name)

            if is_sales_order_stock_notification:
                self.send_email(grp_name='kin_sales.group_receive_sale_order_stock_alert_email',
                                subject='Stock Alert Message from Sales Order (%s) ' % self.name,
                                msg='The Items listed from the (%s), are below the quantities that are to be sold for the sales order (%s).' % (
                                    stock_locations, self.name))

        if msg and is_sales_order_stock_count_error:
            raise UserError(_(msg))

        # Send Email to the Stock Person
        self.send_email(grp_name='kin_sales.group_receive_delivery_stock_transfer_email',
                        subject='A New Delivery transfer document for the sales order (%s) has been created.' % self.name,
                        msg='A New Delivery transfer document for the sales order (%s) has been created.' % self.name)

        # Create Invoice on Ordered Quantity. This should be used for Stock configured with Standard Cost
        is_invoice_before_delivery = self.env['ir.config_parameter'].sudo().get_param('is_invoice_before_delivery',
                                                                                      default=False)

        if is_invoice_before_delivery:
            self.create_advance_invoice()

            # Send Email to the Accountant
            self.send_email(grp_name='kin_sales.group_invoice_before_delivery_email',
                            subject='A New draft advance invoice with source document (%s) has been created for the customer (%s)' % (
                            self.name, self.partner_id.name),
                            msg='A New Draft Invoice with Source Document Number (%s) has been created. Crosscheck and validate the invoice' % self.name)


        #Receive sales order approved email notification
        msg = 'A New sales order has been approved  with source document (%s)  for the customer (%s)' % (
                            self.name, self.partner_id.name)
        self.send_email(grp_name='kin_sales.group_sales_order_approved_email',
                        subject=msg, msg=msg)



        ctx = dict(self._context)
        ctx['is_other_sale'] = True
        res = super(SaleOrderExtend, self.with_context(ctx)).action_confirm()
        return res



    def create_purchase_request(self,sale_stock_loc_ids):
        purchase_request_obj = self.env['purchase.request']
        sale_order_line_obj = self.env['sale.order.line']
        lines =[]
        for sale_order in self :
            for sale_line in sale_order.order_line :
                low_stock_dict = sale_line.check_order_line_qty_location(sale_stock_loc_ids)
                if low_stock_dict :
                    product_id = list(low_stock_dict.keys())[0]
                    lines += [(0,0, {
                        'product_id':product_id,
                        'product_qty': sale_line.product_uom_qty - low_stock_dict[product_id][0],
                        'name' : sale_line.name,
                    })
                    ]
        vals = {
                'origin' : self.name,
                'sale_order_id': self.id,
                'description': self.user_id.name + " was about selling the following listed items with zero stock level. Please request for the items to be purchased from the manager. The sales order reference is: " + self.name ,
                'line_ids':lines
            }
        pr_id = purchase_request_obj.create(vals)
        return pr_id

    def check_sales_product_available_qty(self,sale_stock_loc_ids):
        listdata= []
        product_obj = self.env['product.product']
        ctx = self.env.context.copy()
        quant = self.env['stock.quant']

        for sale_order in self :
            for sale_order_line in sale_order.order_line :
                product = sale_order_line.product_id
                product_id = product.id
                product_name = product.name
                order_line_qty = sale_order_line.product_uom_qty
                qty_available = 0
                if sale_order_line.product_id.type == 'product':
                    for location_id in sale_stock_loc_ids :
                        ctx.update({"location":location_id.id})
                        #res = product_obj.browse([product_id])[0].with_context(ctx)._product_available() #This gives Qty on Hand, which includes reserved qty
                        #qty_available += res[product_id]['qty_available']
                        res = quant._get_available_quantity(sale_order_line.product_id,location_id) #This gives quantity available that excludes reserved qty
                        qty_available += res
                    conv_qty = self.env['uom.uom']._compute_quantity( order_line_qty,sale_order_line.product_uom)
                    if qty_available < conv_qty:
                        listdata.append({product_name:qty_available})
        return listdata


    @api.depends('order_line.invoice_lines')
    def _get_invoiced(self):
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.
        for order in self:
            invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)

    invoice_ids = fields.Many2many("account.move", 'sales_account_move_rel', 'account_id', 'sale_id', string='Invoices', compute="_get_invoiced", readonly=True, copy=False, search="_search_invoice_ids")
    is_request_approval_sent = fields.Boolean(string='Is Request Approval Sent', copy=False, tracking=True)
    is_request_approval_by = fields.Many2one('res.users', string='Requested By', copy=False, tracking=True)
    is_request_approval_date = fields.Datetime(string='Request Approval Date', copy=False, tracking=True)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def check_order_line_qty_location(self,sale_stock_loc_ids):
        ctx = self.env.context.copy()
        quant = self.env['stock.quant']
        product_obj = self.env['product.product']
        for sale_order_line in self :
            product = sale_order_line.product_id
            product_id = product.id
            order_line_qty = sale_order_line.product_uom_qty
            qty_available = 0
            if sale_order_line.product_id.type == 'product':
                for location_id in sale_stock_loc_ids :
                    ctx.update({"location":location_id.id})
                    # res = product_obj.browse([product_id])[0].with_context(ctx)._product_available()
                    # qty_available += res[product_id]['qty_available']
                    res = quant._get_available_quantity(sale_order_line.product_id,location_id)  # This gives quantity available that excludes reserved qty
                    qty_available += res
                conv_qty = self.env['uom.uom']._compute_quantity(order_line_qty, sale_order_line.product_uom)
                if qty_available < conv_qty:
                    return {product_id: (qty_available, conv_qty)}

        return {}