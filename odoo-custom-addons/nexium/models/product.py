# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017 - 2021  Kinsolve Solutions
# Copyright 2017 - 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_charge = fields.Boolean(string='Is a Charge')
    is_petroleum_product = fields.Boolean(string='Is Petroleum Product')
    charges_ids = fields.One2many('charges.nexium', 'product_id',string = 'Charges Percentages')


class Charges(models.Model):
    _name = 'charges.nexium'

    product_charges_id = fields.Many2one('product.product',string='Charges Item')
    charges_percentage = fields.Integer(string='Charges Percentage (%)')
    product_id = fields.Many2one('product.template', string='Product')

