# Copyright 2004-2010 OpenERP SA
# Copyright 2014 Angel Moya <angel.moya@domatix.com>
# Copyright 2015-2020 Tecnativa - Pedro M. Baeza
# Copyright 2016-2018 Tecnativa - Carlos Dauden
# Copyright 2016-2017 LasLabs Inc.
# Copyright 2018 ACSONE SA/NV
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tests import Form
from odoo.tools.translate import _
from dateutil.relativedelta import relativedelta
_logger = logging.getLogger(__name__)


class ContractRecurrencyMixin(models.AbstractModel):
    _inherit = "contract.recurrency.mixin"

    recurring_rule_type = fields.Selection(
        [
            ("daily", "Day(s)"),
            ("weekly", "Week(s)"),
            ("monthly", "Month(s)"),
            ("monthlylastday", "Month(s) last day"),
            ("quarterly", "Quarter(s)"),
            ("semesterly", "Semester(s)"),
            ("yearly", "Year(s)"),
        ],
        default="daily",
        string="Recurrence",
        help="Specify Interval for automatic invoice generation.",
    )

    recurring_interval = fields.Integer(
        default=30,
        string="Invoice Every",
        help="Invoice every (Days/Week/Month/Year)",
    )

    next_reminder_date = fields.Date(string="Next Reminder Date")





class ContractContract(models.Model):
    _inherit = "contract.contract"

    def _prepare_recurring_invoices_values(self, date_ref=False):
        """
        This method builds the list of invoices values to create, based on
        the lines to invoice of the contracts in self.
        !!! The date of next invoice (recurring_next_date) is updated here !!!
        :return: list of dictionaries (invoices values)
        """
        invoices_values = []
        for contract in self:
            if not date_ref:
                date_ref = contract.recurring_next_date
            if not date_ref:
                # this use case is possible when recurring_create_invoice is
                # called for a finished contract
                continue
            contract_lines = contract._get_lines_to_invoice(date_ref)
            if not contract_lines:
                continue
            invoice_vals, move_form = contract._prepare_invoice(date_ref)
            invoice_vals["invoice_line_ids"] = []
            for line in contract_lines:
                end_date = line.next_period_date_end
                self.next_reminder_date = end_date - relativedelta(days=7)
                name = '%s starting from %s to %s' % (line.display_name,line.next_period_date_start.strftime('%d-%m-%Y'),end_date.strftime('%d-%m-%Y'))
                invoice_line_vals = line._prepare_invoice_line(move_form=move_form)
                invoice_line_vals['name'] = name
                if invoice_line_vals:
                    # Allow extension modules to return an empty dictionary for
                    # nullifying line. We should then cleanup certain values.
                    del invoice_line_vals["company_id"]
                    del invoice_line_vals["company_currency_id"]
                    invoice_vals["invoice_line_ids"].append((0, 0, invoice_line_vals))
            invoices_values.append(invoice_vals)
            # Force the recomputation of journal items
            del invoice_vals["line_ids"]
            contract_lines._update_recurring_next_date()
        return invoices_values




