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

class CustomerStocKReport(models.TransientModel):
    _name = 'report.kin_loading.report_customer_stock'
    _inherit = 'report.report_xlsx.abstract'


    def _get_data(self,product_id, partner_id,type):

        where_partner = "sol.order_partner_id = '%s' AND" % (partner_id)
        where_prod = "sol.product_id = '%s' AND" % (product_id)

        where_type = ''
        if type == 'is_throughput':
            where_type = "sol.is_throughput_order = True AND"
        elif type == 'is_internal_use':
            where_type = "sol.is_internal_use_order = True AND"
        elif type == 'is_indepot':
            where_type = "sol.is_throughput_order = False AND sol.is_internal_use_order = False AND"
        elif type == 'all':
            where_type = ""

        # LEFT JOIN works similar to INNER JOIN but with the extra advantage of showing empty join parameter fields (uncompulsory join fields). It is good for join fields that don't have value. It will still show the records. Unlike INNER JOIN (for compulsory join fields) which will omit those records
        sql_statement = """
            SELECT
                date_order , qty_to_invoice, product_uom_qty,
                qty_invoiced, price_subtotal, price_reduce, qty_delivered, price_total, product_ticket_qty,
               ticket_remaining_qty,  ticket_created_qty, transfer_created_qty, cancelled_remaining_qty, 
               unloaded_balance_qty,  balance_qty,
               sol.name as prod_name,sol.product_id, customer.name as customer_name , customer.ref as customer_ref
            FROM sale_order_line as sol
            LEFT JOIN sale_order ON sol.order_id = sale_order.id
            LEFT JOIN res_partner as customer ON sol.order_partner_id = customer.id
            WHERE
             """ + where_type + """
             """ + where_partner + """
             """ + where_prod + """
             customer.customer_rank != 0 AND
             sol.state NOT IN ('draft','cancel')
            """
        self.env.cr.execute(sql_statement)
        dictAll = self.env.cr.dictfetchall()

        return dictAll


    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id

        product_ids = data['form']['product_ids']
        if not product_ids :
            pro_ids = self.env['product.product'].search([('type','=','product')])
            for pr_id in pro_ids:
                product_ids.append(pr_id.id)

        partner_ids = data['form']['partner_ids']
        if not partner_ids:
            part_ids = self.env['res.partner'].search([('customer_rank', '!=', 0)])
            for part_id in part_ids:
                partner_ids.append(part_id.id)


        report_worksheet = workbook.add_worksheet('Customer Stock Report')
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 24})
        title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        head_format = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10,'bg_color':'blue','color':'white'})
        head_format.set_num_format('#,#0.00')
        head_format_total = workbook.add_format({'bold': True, 'border': 1})
        head_sub_format_indent1 = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        head_sub_format_indent1.set_indent(1)
        cell_total_description = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_wrap_format = workbook.add_format({'valign': 'vjustify', 'font_size': 10, 'border': 1})
        cell_amount = workbook.add_format({'border': 1, 'font_size': 10})
        cell_amount.set_num_format('#,#0.00')
        cell_total_currency = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_total_currency.set_num_format('#,#0.00')
        cell_number = workbook.add_format({'border': 1, 'font_size': 10})
        cell_number.set_num_format('#,#')

        # Header Format
        report_worksheet.set_row(0, 30)  # Set row height
        report_worksheet.merge_range(0, 0, 0, 10, user_company.name, header_format)

        # Title Format
        report_worksheet.set_row(2, 20)
        report_worksheet.merge_range(2, 0, 2, 10, 'Customer Stock Report', title_format)

        # Period
        report_worksheet.merge_range(3, 0, 3, 10, 'Period: All', title_format)

        col = 0
        row = 5
        report_worksheet.set_column(0, 0, 5)
        report_worksheet.set_column(1, 1, 10)
        report_worksheet.set_column(2, 2, 15)
        report_worksheet.set_column(3, 12, 10)

        partner_obj = self.env['res.partner']
        product_obj =  self.env['product.product']
        type = data['form']['type']
        for product_id in product_ids :
            report_worksheet.set_row(row, 20)
            row += 2
            product_name = product_obj.browse(product_id).name
            report_worksheet.merge_range(row, col, row, 9, 'PRODUCT: '+ product_name, title_format)
            row += 1

            for part_id in partner_ids :
                list_dicts = self._get_data(product_id,part_id,type)
                row += 2
                partner_name = partner_obj.browse(part_id).name
                report_worksheet.merge_range(row, col, row, 9, partner_name, title_format)
                row += 2

                report_worksheet.write_row(row, col, (
                'S/N', 'Order Date', 'Ordered Qty.', 'Transferred Qty.', 'Cancelled Qty.',
                'Un-Ticketed Qty.', 'Ticketed Qty.', 'Loaded Qty.', 'Un-loaded Qty.', 'Balance Qty.', 'Invoiced',
                'Un-Invoiced', 'Sub-total'), head_format)
                row += 1
                total_qty = 0
                balance_qty = 0
                first_row = row
                sn = 0

                for list_dict in list_dicts:
                    sn += 1
                    report_worksheet.write(row, 0, sn, cell_wrap_format)
                    #report_worksheet.write(row, 1, list_dict['customer_ref'], cell_wrap_format)
                    # report_worksheet.write(row, 2, list_dict['customer_name'], cell_wrap_format)
                    report_worksheet.write(row, 1, list_dict['date_order'] and list_dict['date_order'].strftime('%d-%m-%Y'), cell_wrap_format) or False
                    report_worksheet.write(row, 2, list_dict['product_uom_qty'], cell_number)
                    report_worksheet.write(row, 3, list_dict['transfer_created_qty'], cell_number)
                    report_worksheet.write(row, 4, list_dict['cancelled_remaining_qty'], cell_number)
                    report_worksheet.write(row, 5, list_dict['ticket_remaining_qty'], cell_number)
                    report_worksheet.write(row, 6, list_dict['ticket_created_qty'], cell_number)
                    report_worksheet.write(row, 7, list_dict['qty_delivered'], cell_number)
                    report_worksheet.write(row, 8, list_dict['unloaded_balance_qty'], cell_number)
                    report_worksheet.write(row, 9, list_dict['balance_qty'], cell_number)
                    report_worksheet.write(row, 10, list_dict['qty_invoiced'], cell_amount)
                    report_worksheet.write(row, 11, list_dict['qty_to_invoice'], cell_amount)
                    report_worksheet.write(row, 12, list_dict['price_subtotal'], cell_amount)
                    row += 1
                    total_qty += list_dict['product_uom_qty']
                    balance_qty += list_dict['balance_qty']
                last_row = row
                a1_notation_ref = xl_range(first_row, 2, last_row, 2)
                report_worksheet.write(row, 2, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_qty)
                bal_notation_ref = xl_range(first_row, 9, last_row, 9)
                report_worksheet.write(row, 9, '=SUM(' + bal_notation_ref + ')', cell_total_currency, balance_qty)
                row += 1
        return

