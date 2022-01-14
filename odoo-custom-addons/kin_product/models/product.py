# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        if not self.env.user.has_group('kin_product.group_allow_create_product'):
            raise UserError('Sorry, you are not allowed to create a product')
        return super(ProductProduct, self).create(vals)

    # def write(self, vals):
    #     if not self.env.user.has_group('kin_product.group_allow_edit_product'):
    #         raise UserError('Sorry, you are not allowed to edit this product')
    #     return super(ProductProduct, self).write(vals)

    def unlink(self):
        for rec in self:
            if not self.env.user.has_group('kin_product.group_allow_delete_product'):
                raise UserError(
                    'Sorry, you are not allowed to delete this product')
        return super(ProductProduct, self).unlink()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        if not self.env.user.has_group('kin_product.group_allow_create_product'):
            raise UserError(
                'Sorry, you are not allowed to create a product template')
        return super(ProductTemplate, self).create(vals)

    # def write(self, vals):
    #     if not self.env.user.has_group('kin_product.group_allow_edit_product'):
    #         raise UserError(
    #             'Sorry, you are not allowed to edit this product template')
    #     return super(ProductTemplate, self).write(vals)

    def unlink(self):
        for rec in self:
            if not self.env.user.has_group('kin_product.group_allow_delete_product'):
                raise UserError(
                    'Sorry, you are not allowed to delete this product template')
        return super(ProductTemplate, self).unlink()
