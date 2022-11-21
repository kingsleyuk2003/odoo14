# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from datetime import datetime, timedelta , date

class HRBank(models.Model):
    _name = 'hr.bank'

    name = fields.Char(string='Bank')

class HRBusinessUnit(models.Model):
    _name = 'hr.business.unit'

    name = fields.Char(string='Business Unit')


class hrExtend(models.Model):
    _inherit = 'hr.employee'

    @api.depends('employment_date')
    def _compute_service_days(self):
        for rec in self:
            if rec.employment_date :
                rec.length_of_service_days = (date.today() - rec.employment_date).days
            else:
                rec.length_of_service_days = 0


    staff_no = fields.Char(string="Staff No.")
    employment_date = fields.Date('Employment Date')
    grade_level = fields.Selection([('mgt', 'Management'), ('non-mgt', 'Non Management'), ('director', 'Director')],
                                         string='Grade Level')
    category = fields.Selection([('permanent', 'PERMANENT'), ('contract', 'CONTRACT')], string='Category')
    is_offer_letter = fields.Boolean(string='Has Offer Letter')
    offer_letter = fields.Binary(string='Offer Letter', attachment=True)
    is_confirmation_letter = fields.Boolean(string='Has Confirmation Letter')
    confirmation_letter = fields.Binary(string='Confirmation Letter', attachment=True)
    is_employee_file = fields.Boolean(string='Has Employee File')
    employee_file = fields.Binary(string='Employee File', attachment=True)
    is_resume = fields.Boolean(string='Has Updated Resume/CV')
    resume = fields.Binary(string='Updated Resume/CV')
    is_edu_qualifications = fields.Boolean(string='Has Educational Qualifications')
    edu_qualifications = fields.Binary(string='Educational Qualifications')
    is_prof_qualifications = fields.Boolean(string='Has Professional Qualifications')
    prof_qualifications = fields.Binary(string='Professional Qualifications')
    is_valid_id = fields.Boolean(string='Has Valid ID')
    valid_id = fields.Binary(string='Valid ID')
    is_bio_data_form = fields.Boolean(string='Has Bio data Form')
    bio_data_form = fields.Binary(string='Bio data Form')
    business_unit = fields.Many2one('hr.business.unit', string='Business Unit')
    length_of_service_days = fields.Char(string='Length of Service (Days)',compute='_compute_service_days')


class HRContract(models.Model):
    _inherit = 'hr.contract'

    paye = fields.Monetary(string="P.A.Y.E")
    lc = fields.Monetary(string="Logistics / Call Allowances")
    bank_account_no = fields.Char(string='Bank Account No.')
    bank_id = fields.Many2one('hr.bank', string='Bank')