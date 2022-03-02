# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update({
            'is_select_sales_team': self.env['ir.config_parameter'].sudo().get_param('is_select_sales_team', default=False),
            'is_contraint_sales_order_stock': self.env['ir.config_parameter'].sudo().get_param('is_contraint_sales_order_stock', default=False),
            'is_sales_order_stock_notification': self.env['ir.config_parameter'].sudo().get_param('is_sales_order_stock_notification', default=False),
            'is_sales_order_stock_count_error': self.env['ir.config_parameter'].sudo().get_param('is_sales_order_stock_count_error', default=False),
            'is_send_stock_notification': self.env['ir.config_parameter'].sudo().get_param('is_send_stock_notification', default=False),
            'is_invoice_before_delivery': self.env['ir.config_parameter'].sudo().get_param('is_invoice_before_delivery', default=False),
            'is_post_invoice_before_delivery': self.env['ir.config_parameter'].sudo().get_param('is_post_invoice_before_delivery',default=False),
            'is_send_invoice_notification': self.env['ir.config_parameter'].sudo().get_param('is_send_invoice_notification', default=False),
            'is_sales_order_stock_purchase_request': self.env['ir.config_parameter'].sudo().get_param('is_sales_order_stock_purchase_request', default=False),
            'is_po_check': self.env['ir.config_parameter'].sudo().get_param('is_po_check', default=False),
            'validity_date_interval': self.env['ir.config_parameter'].sudo().get_param('validity_date_interval', default=0),
            'is_error_quote_after_expiration_date': self.env['ir.config_parameter'].sudo().get_param('is_error_quote_after_expiration_date', default=False),
            'is_send_expiry_email_quote_notification': self.env['ir.config_parameter'].sudo().get_param('is_send_expiry_email_quote_notification', default=False),
            'is_send_expiry_reminder_email_quote_notification': self.env['ir.config_parameter'].sudo().get_param('is_send_expiry_reminder_email_quote_notification', default=False),
            'is_delete_quote_after_expiration_date': self.env['ir.config_parameter'].sudo().get_param('is_delete_quote_after_expiration_date', default=False),
        })
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('is_select_sales_team', self.is_select_sales_team)
        self.env['ir.config_parameter'].sudo().set_param('is_contraint_sales_order_stock', self.is_contraint_sales_order_stock)
        self.env['ir.config_parameter'].sudo().set_param('is_sales_order_stock_notification', self.is_sales_order_stock_notification)
        self.env['ir.config_parameter'].sudo().set_param('is_send_stock_notification', self.is_send_stock_notification)
        self.env['ir.config_parameter'].sudo().set_param('is_sales_order_stock_count_error', self.is_sales_order_stock_count_error)
        self.env['ir.config_parameter'].sudo().set_param('is_invoice_before_delivery', self.is_invoice_before_delivery)
        self.env['ir.config_parameter'].sudo().set_param('is_post_invoice_before_delivery', self.is_post_invoice_before_delivery)
        self.env['ir.config_parameter'].sudo().set_param('is_send_invoice_notification', self.is_send_invoice_notification)
        self.env['ir.config_parameter'].sudo().set_param('is_sales_order_stock_purchase_request', self.is_sales_order_stock_purchase_request)
        self.env['ir.config_parameter'].sudo().set_param('is_po_check', self.is_po_check)
        self.env['ir.config_parameter'].sudo().set_param('validity_date_interval', self.validity_date_interval)
        self.env['ir.config_parameter'].sudo().set_param('is_error_quote_after_expiration_date', self.is_error_quote_after_expiration_date)
        self.env['ir.config_parameter'].sudo().set_param('is_send_expiry_email_quote_notification', self.is_send_expiry_email_quote_notification)
        self.env['ir.config_parameter'].sudo().set_param('is_delete_quote_after_expiration_date', self.is_delete_quote_after_expiration_date)
        self.env['ir.config_parameter'].sudo().set_param('is_send_expiry_reminder_email_quote_notification',
                                                         self.is_send_expiry_reminder_email_quote_notification)

    is_select_sales_team = fields.Boolean(string='Is Sales Channel', help="By default, the system select the default sales team, but if the box is checked, then it clear the selection, for users to select themselves manually")
    is_contraint_sales_order_stock = fields.Boolean(string='Is Sales-Stock Count Check', help='Do not allow confirmation of sales if stock is lesser than ordered quantity during Sales order confirmation')
    is_sales_order_stock_notification = fields.Boolean(string='Is Email Notification for Low Sales Stock', help='Send Email Notification if stock is lesser than ordered quantity during Sales order confirmation')
    is_sales_order_stock_count_error = fields.Boolean(string='Is Raise Error on Low Sales Stock', help='Raise System Error if stock is lesser than ordered quantity during Sales order confirmation')
    is_sales_order_stock_purchase_request = fields.Boolean(string="Create Purchase Request from Sales on Low Stock",help='Create a Purchase Request, if stock is lesser than ordered quantity during Sales order confirmation')
    is_send_stock_notification = fields.Boolean(string='Is Daily Stock Minimum',help='Send Daily Stock Minimum Notification Report')
    is_invoice_before_delivery = fields.Boolean(string='Is Advance Invoice Before Delivery',help='Create Advance Invoice from Sales Ordered Qty. before Delivery, this should be used for products with fixed/standard costing method')
    is_post_invoice_before_delivery = fields.Boolean(string='Is Post Advance Invoice Before Delivery', help='Post Created Advance Invoice from Sales Ordered Qty. before Delivery')
    is_send_invoice_notification = fields.Boolean(string='Is Send Invoice Email Notification on Sales ordered invoicing policy.',help='Send Invoice Email Notification on Sales ordered quantity. This should be used for products with fixed/standard costing method')
    is_po_check = fields.Boolean(string='Is PO Check', help='Forces Sales Person to Enter a PO Reference', default=True)
    validity_date_interval = fields.Integer(string='Sales Quote Expiry Reminder Interval', help='Reminder Days Before Sales Quote Expires', default=3)
    is_error_quote_after_expiration_date = fields.Boolean(string='Is Error Alert after Quote Expiration', help='Show UserError Alert after Expiration Date')
    is_send_expiry_email_quote_notification = fields.Boolean(string='Is Email Expiration Quote Notification ', help='Send Expiration Email Quote Notification', default=True)
    is_delete_quote_after_expiration_date = fields.Boolean(string='Is Delete Quote after Expiration',help='Delete Sales Quotation after Expiration Date')
    is_send_expiry_reminder_email_quote_notification = fields.Boolean(string='Is Send Expiry Reminder Days Email Notification ',
                                                             help='Send Expiry Reminder Days Email Notification',
                                                             default=True)
