# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import api, fields, models, _

class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_expense = fields.Boolean(string='Is Expense')