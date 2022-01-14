# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2021  Kinsolve Solutions
# Copyright 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from odoo import api, fields, models
from datetime import datetime
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell


class BankStatement(models.AbstractModel):
    _name = 'report.kin_bank_reconcile.report_bank_statement_excel'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, objects):

        obj_id = data['active_ids'][0]
        obj = self.env['bank.statement'].browse(obj_id)

        report_worksheet = workbook.add_worksheet('Bank Reconciliation Statement')
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 24})
        title_format = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'font_size': 14})
        head_format = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        head_format.set_num_format('#,#00.00')
        head_format_total = workbook.add_format({'bold': True, 'border': 1})
        head_sub_format_indent1 = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        head_sub_format_indent1.set_indent(1)
        cell_total_description = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_wrap_format = workbook.add_format({'valign': 'vjustify', 'font_size': 10, 'border': 1})
        cell_amount = workbook.add_format({'border': 1, 'font_size': 10})
        cell_amount.set_num_format('#,#00.00')
        cell_total_currency = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_total_currency.set_num_format('#,#00.00')

        # Title Format
        report_worksheet.set_row(1, 20) #set height for row 1

        report_worksheet.merge_range(1, 0, 1, 7, '%s' % (obj.company_id.name), title_format)
        report_worksheet.merge_range(2, 0, 2, 7, 'Bank Reconciliation Statement'  , title_format)
        report_worksheet.merge_range(3, 0, 3, 7, '', title_format)
        report_worksheet.merge_range(4, 0,4, 3, 'Bank: %s' % (obj.account_id.name), head_format)
        if obj.start_date:
            start_date_time_format = datetime.strptime(obj.start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            report_worksheet.merge_range(4, 4, 4, 5, 'Start Date: %s' % (start_date_time_format), head_format)
        if obj.end_date:
            end_date_time_format = datetime.strptime(obj.end_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            report_worksheet.merge_range(4, 6, 4, 7, 'End Date: %s' % (end_date_time_format), head_format)

        report_worksheet.merge_range(5, 0, 5, 7, 'Balance as per Company Books: %s %s' % (obj.company_id.currency_id.symbol,'{:,.2f}'.format(obj.gl_balance)), cell_total_currency)
        report_worksheet.merge_range(6, 0, 6, 7, 'Balance as per Bank: %s %s' % (obj.company_id.currency_id.symbol,'{:,.2f}'.format(obj.bank_reconciled_balance)),cell_total_currency)
        report_worksheet.merge_range(7, 0, 7, 7, 'Amounts not reflected in Bank: %s %s' % (obj.company_id.currency_id.symbol,'{:,.2f}'.format(obj.unreconciled_balance)),cell_total_currency)
        report_worksheet.merge_range(8, 0, 8, 7, '', title_format)
        col = 0
        row = 8
        row += 2
        report_worksheet.set_column(0,0,10)
        report_worksheet.set_column(1, 1,15)
        report_worksheet.set_column(2, 2, 25)
        report_worksheet.set_column(3, 3,15)
        report_worksheet.set_column(4, 4, 25)
        report_worksheet.set_column(5, 5, 5)
        report_worksheet.set_column(6, 6, 15)
        report_worksheet.set_column(7, 7, 5)
        report_worksheet.write_row(row, col, (
        'Date', 'Journal Entry', 'Label', 'Partner Reference', 'Partner', 'Amt. Curr.', 'Amount','Reconcile'), head_format)
        row += 1

        for line in obj.move_line_ids :
            report_worksheet.write(row, 0,  datetime.strptime(str(line.date), '%Y-%m-%d').strftime('%d/%m/%Y'), cell_wrap_format)
            report_worksheet.write(row, 1, line.move_id.name, cell_wrap_format)
            report_worksheet.write(row, 2, line.name, cell_wrap_format)
            report_worksheet.write(row, 3, line.ref if line.ref else '', cell_wrap_format)
            report_worksheet.write(row, 4, line.partner_id.name if line.partner_id.name else '', cell_wrap_format)
            report_worksheet.write(row, 5, line.amount_currency, cell_amount)
            report_worksheet.write(row, 6, line.balance, cell_amount)
            report_worksheet.write(row, 7, 'True' if line.is_bank_reconciled else 'False', cell_wrap_format)
            row += 1
        return



