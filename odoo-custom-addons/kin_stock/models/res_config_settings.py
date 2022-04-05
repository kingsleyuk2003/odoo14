# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update({
            'create_vendor_bill': self.env['ir.config_parameter'].sudo().get_param('create_vendor_bill', default=False),
            'create_customer_invoice': self.env['ir.config_parameter'].sudo().get_param('create_customer_invoice', default=False),
            'post_vendor_bill':self.env['ir.config_parameter'].sudo().get_param('post_vendor_bill', default=False),
            'post_customer_invoice': self.env['ir.config_parameter'].sudo().get_param('post_customer_invoice', default=False),
            'allow_over_transfer': self.env['ir.config_parameter'].sudo().get_param('allow_over_transfer',default=False),
        })
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('create_vendor_bill', self.create_vendor_bill)
        self.env['ir.config_parameter'].sudo().set_param('create_customer_invoice', self.create_customer_invoice)
        self.env['ir.config_parameter'].sudo().set_param('post_vendor_bill', self.post_vendor_bill)
        self.env['ir.config_parameter'].sudo().set_param('post_customer_invoice', self.post_customer_invoice)
        self.env['ir.config_parameter'].sudo().set_param('allow_over_transfer', self.allow_over_transfer)


    create_vendor_bill = fields.Boolean("Create Vendor Bill")
    create_customer_invoice = fields.Boolean("Create Customer Invoice")
    post_vendor_bill = fields.Boolean("Post Vendor Bill")
    post_customer_invoice = fields.Boolean("Post Customer Invoice")
    allow_over_transfer = fields.Boolean('Allow Over Transfer in Stock Picking')

