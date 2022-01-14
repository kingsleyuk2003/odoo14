# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update({
            'attn': self.env['ir.config_parameter'].sudo().get_param('attn', default=False),
            'role': self.env['ir.config_parameter'].sudo().get_param('role', default=False),
            'to_address': self.env['ir.config_parameter'].sudo().get_param('to_address', default=False),
            'attn_tank': self.env['ir.config_parameter'].sudo().get_param('attn_tank', default=False),
            'role_tank': self.env['ir.config_parameter'].sudo().get_param('role_tank', default=False),
            'to_address_tank': self.env['ir.config_parameter'].sudo().get_param('to_address_tank', default=False)
        })
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'attn', self.attn)
        self.env['ir.config_parameter'].sudo().set_param(
            'role', self.role)
        self.env['ir.config_parameter'].sudo().set_param(
            'to_address', self.to_address)
        self.env['ir.config_parameter'].sudo().set_param(
            'attn_tank', self.attn_tank)
        self.env['ir.config_parameter'].sudo().set_param(
            'role_tank', self.role_tank)
        self.env['ir.config_parameter'].sudo().set_param(
            'to_address_tank', self.to_address_tank)

    attn = fields.Char(string="Attn")
    role = fields.Char(string="Role")
    to_address = fields.Char(string="To Address")
    attn_tank = fields.Char(string="Attn")
    role_tank = fields.Char(string="Role")
    to_address_tank = fields.Char(string="To Address")
