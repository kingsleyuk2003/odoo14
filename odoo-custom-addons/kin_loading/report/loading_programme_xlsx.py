# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2022  Kinsolve Solutions
# Copyright 2022 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from odoo import api, fields, models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell

class LoadingProgrammeReport(models.TransientModel):
    _name = 'report.kin_loading.loading_programme_excel'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects):
        prog_obj = objects

        report_worksheet = workbook.add_worksheet('Loading Programme Excel')
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
        report_worksheet.set_row(1, 20)
        date_time_format = prog_obj.programme_date.strftime('%d/%m/%Y')
        report_worksheet.merge_range(1, 0, 1, 7,
                                     '%s' % (prog_obj.env.user.company_id.name),
                                     title_format)
        report_worksheet.merge_range(3, 0, 3, 7,
                                     'LOADING PROGRAMME %s' % (prog_obj.name),
                                     title_format)
        report_worksheet.merge_range(5, 0,5, 7,
                                     'Date: %s          PRODUCT: %s' % (date_time_format,prog_obj.product_id.name),
                                     head_format)

        col = 0
        row = 1
        row += 6
        report_worksheet.set_column(0, 0, 5)
        report_worksheet.set_column(1, 1, 15)
        report_worksheet.set_column(2, 2, 30)
        report_worksheet.set_column(3, 3, 10)
        report_worksheet.set_column(4, 4, 10)
        report_worksheet.set_column(5, 6, 40)
        report_worksheet.set_column(7, 7, 15)
        report_worksheet.write_row(row, col, (
            'S/N', 'TICKET NO.', 'CUSTOMER', 'QUANTITY.','TRUCK NO.','DESTINATION', 'DPR NO.'), head_format)
        row += 1
        sn = 0
        total_qty = 0
        first_row = row
        for ticket in prog_obj.ticket_ids:
            sn += 1
            report_worksheet.write(row, 0, sn, cell_wrap_format)
            report_worksheet.write(row, 1, ticket.name, cell_wrap_format)
            report_worksheet.write(row, 2, ticket.partner_id.name, cell_wrap_format)
            report_worksheet.write(row, 3, ticket.ticket_load_qty, cell_amount)
            report_worksheet.write(row, 4, ticket.truck_no, cell_wrap_format)
            report_worksheet.write(row, 5, ticket.receiving_station_address, cell_wrap_format)
            report_worksheet.write(row, 6, ticket.dpr_no, cell_wrap_format)
            total_qty += ticket.ticket_load_qty
            row += 1
        last_row = row
        a1_notation_ref = xl_range(first_row, 3, last_row, 3)
        report_worksheet.write(row, 2,'Total QTY.',head_format)
        report_worksheet.write(row, 3, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_qty)
