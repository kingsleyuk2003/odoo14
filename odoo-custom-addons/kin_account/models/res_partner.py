# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019-2021  Kinsolve Solutions
# Copyright 2019-2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _

class ResPartnerExtend(models.Model):
    _inherit = 'res.partner'

    def name_get(self): # Works when you are reading the field name. e.g. when  tree view is loaded or form view is loaded
        result = []
        for partner in self:
            if partner.ref:
                strf = "%s - %s" % (partner.ref, partner.name)
                item = (partner.id, strf)
                result.append(item)
            else:
                result.append((partner.id, partner.name))
        return result

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100): # Works when you are searching for a field name on a many2one field or the search bar. it depicts how you you want to search
    #     args = args or []
    #     recs = self.browse()  # Initializes the variable, you can use recs = []
    #     if name:
    #         recs = self.search(['|', ('name', '=', name),('ref','=',name)] + args, limit=limit)
    #     if not recs:
    #         recs = self.search(['|', ('name', operator, name),('ref',operator,name)] + args, limit=limit)
    #     return recs.name_get()


