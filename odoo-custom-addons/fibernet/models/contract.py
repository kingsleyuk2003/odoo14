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


    @api.onchange('date_start')
    def onchange_date_start(self):
        self.recurring_next_date = self.date_start + relativedelta(days=23)

    @api.onchange('recurring_next_date')
    def onchange_next_date(self):
        self.next_due_date = self.recurring_next_date + relativedelta(days=7)

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

    next_due_date = fields.Date(string="Next Due Date")



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
                nps = self.recurring_next_date + relativedelta(days=7)
                npe = nps + relativedelta(days=30)
                self.recurring_next_date = nps + relativedelta(days=23)
                self.next_due_date = self.recurring_next_date + relativedelta(days=7)
                name = '%s starting from %s to %s' % (line.name,nps.strftime('%d-%m-%Y'),npe.strftime('%d-%m-%Y'))
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
            #contract_lines._update_recurring_next_date()
        return invoices_values



    def action_view_ticket(self):
        ticket_ids = self.mapped('ticket_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("kin_helpdesk.action_view_all_tickets")

        if len(ticket_ids) > 1:
            action['domain'] = [('id', 'in', ticket_ids.ids)]
        elif len(ticket_ids) == 1:
            form_view = [(self.env.ref('kin_helpdesk.ticket_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = ticket_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        #action['target'] = 'new'

        context = {
            #'default_move_type': 'out_invoice',
        }
        # if len(self) == 1:
        #     context.update({
        #         'default_partner_id': self.partner_id.id,
        #         'default_partner_shipping_id': self.partner_shipping_id.id,
        #         'default_invoice_payment_term_id': self.payment_term_id.id or self.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
        #         'default_invoice_origin': self.mapped('name'),
        #         'default_user_id': self.user_id.id,
        #     })
        action['context'] = context
        return action

    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        for rec in self:
            rec.ticket_count = len(rec.ticket_ids)



    ticket_ids = fields.One2many('kin.ticket', 'contract_id', string='Tickets')
    ticket_count = fields.Integer(compute="_compute_ticket_count", string='# of Ticket', copy=False, default=0)

