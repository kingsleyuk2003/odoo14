# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from datetime import datetime, timedelta
from odoo import SUPERUSER_ID
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from urllib.parse import urlencode
from urllib.parse import urljoin
import  time
from odoo import tools, api


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    def _default_wifiber_bank_journal_id(self):
        default_company_id = self.default_get(['company_id'])['company_id']
        return self.env['account.journal'].search([('type', 'in', ['cash', 'bank']),('company_id', '=', default_company_id), ('is_expense', '=', True) ], limit=1)

    payment_mode = fields.Selection(default='company_account')
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal',
                                      states={'done': [('readonly', True)], 'post': [('readonly', True)]},
                                      check_company=True,
                                      domain="[('type', 'in', ['cash', 'bank']), ('company_id', '=', company_id)]",
                                      default=_default_wifiber_bank_journal_id,
                                      help="The payment method used when the expense is paid by the company.")

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    payment_mode = fields.Selection(default='company_account')
