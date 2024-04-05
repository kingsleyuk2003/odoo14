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
    _name = 'report.kin_loading.report_customer_stock_summary'
    _inherit = 'report.report_xlsx.abstract'

    def _get_data(self,form):
        partner_id = form['partner_id']
        product_ids = form['product_ids']
        type = form['type']

        where_type = ''
        if type == 'is_throughput':
            where_type = "sol.is_throughput_order = True AND"
        elif type == 'is_internal_use':
            where_type = "sol.is_internal_use_order = True AND"
        elif type == 'is_indepot':
            where_type = "sol.is_throughput_order = False AND sol.is_internal_use_order = False AND"
        elif type == 'all':
            where_type = ""

        where_partner = ''
        if partner_id :
            where_partner = "sol.order_partner_id = '%s' AND" % (partner_id[0])


        where_prod = ''
        if product_ids:
            where_prod = "sol.product_id in (%s) AND" % ','.join(str(pr_id) for pr_id in product_ids)

        # LEFT JOIN works similar to INNER JOIN but with the extra advantage of showing empty join parameter fields (uncompulsory join fields). It is good for join fields that don't have value. It will still show the records. Unlike INNER JOIN (for compulsory join fields) which will omit those records
        sql_statement = """
            SELECT
               sum(sol.qty_to_invoice) as qty_to_invoice, sum(sol.product_uom_qty) as product_uom_qty,
               sum(sol.qty_invoiced) as qty_invoiced,
               sum(sol.price_subtotal) as price_subtotal, sum(sol.price_reduce) as price_reduce,
               sum(sol.qty_delivered) as qty_delivered, sum(sol.price_total) as price_total, sum(sol.product_ticket_qty) as product_ticket_qty,
               sum(sol.ticket_remaining_qty) as ticket_remaining_qty, sum(sol.ticket_created_qty) as ticket_created_qty,
               sum(sol.transfer_created_qty) as transfer_created_qty, sum(sol.cancelled_remaining_qty) as cancelled_remaining_qty,
               sum(sol.unloaded_balance_qty) as unloaded_balance_qty, sum(sol.balance_qty) as balance_qty,
               sol.name as prod_name,sol.product_id, customer.name as customer_name , customer.ref as customer_ref
            FROM sale_order_line as sol
            LEFT JOIN res_partner as customer ON sol.order_partner_id = customer.id
            WHERE
             """ + where_type +"""
             """ + where_partner +"""
             """ + where_prod + """
             sol.state NOT IN ('draft','cancel')
            GROUP BY customer_name , customer_ref, product_id, prod_name
            """
        self.env.cr.execute(sql_statement)
        dictAll = self.env.cr.dictfetchall()

        return dictAll


    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        list_dicts = self._get_data(data['form'])

        product_ids = data['form']['product_ids']
        if not product_ids :
            pro_ids = self.env['product.product'].search([('type','=','product')])
            for pr_id in pro_ids:
                product_ids.append(pr_id.id)


        report_worksheet = workbook.add_worksheet('Customer Stock Summary Report')
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
        report_worksheet.merge_range(0, 0, 0, 10, self.env.company.name, header_format)

        # Title Format
        report_worksheet.set_row(2, 20)
        type = data['form']['type']
        if type == 'is_throughput':
            report_worksheet.merge_range(2, 0, 2, 10, 'Throughput Customer Stock Summary Report', title_format)
        elif type == 'is_internal_use':
            report_worksheet.merge_range(2, 0, 2, 10, 'Internal Use Customer Stock Summary Report', title_format)
        elif type == 'is_indepot':
            report_worksheet.merge_range(2, 0, 2, 10, 'In Depot Customer Stock Summary Report', title_format)
        elif type == 'all':
            report_worksheet.merge_range(2, 0, 2, 10, 'All Customer Stock Summary Report', title_format)


        # Period
        report_worksheet.merge_range(3, 0, 3, 10, 'Period: All', title_format)

        col = 0
        row = 5
        report_worksheet.set_column(0, 0, 5)
        report_worksheet.set_column(1, 1, 10)
        report_worksheet.set_column(2, 2, 25)
        report_worksheet.set_column(3, 17, 10)

        product_obj =  self.env['product.product']
        for product_id in product_ids :
            report_worksheet.set_row(row, 20)
            row += 2
            product_name = product_obj.browse(product_id).name
            report_worksheet.merge_range(row, col, row, 9, product_name, title_format)
            row += 2

            report_worksheet.write_row(row, col, ('S/N', 'Customer ID' , 'Customer', 'Product.', 'Ordered Qty.', 'Transferred Qty.', 'Cancelled Qty.', 'Un-Ticketed Qty.' , 'Ticketed Qty.', 'Loaded Qty.', 'Un-loaded Qty.', 'Balance Qty.', 'Invoiced', 'Un-Invoiced' ,'Sub-total' ) , head_format)
            row += 1
            total_qty = 0
            balance_qty = 0
            first_row = row
            a1_notation_total_qty_start = xl_rowcol_to_cell(row, 1)
            sn = 0
            for list_dict in list_dicts:
                if list_dict['product_id'] == product_id :
                    sn += 1
                    report_worksheet.write(row, 0, sn,cell_wrap_format)
                    report_worksheet.write(row, 1, list_dict['customer_ref'], cell_wrap_format)
                    report_worksheet.write(row, 2, list_dict['customer_name'], cell_wrap_format)
                    report_worksheet.write(row, 3, list_dict['prod_name'], cell_wrap_format)
                    report_worksheet.write(row, 4, list_dict['product_uom_qty'], cell_wrap_format)
                    report_worksheet.write(row, 5, list_dict['transfer_created_qty'], cell_number)
                    report_worksheet.write(row, 6, list_dict['cancelled_remaining_qty'], cell_number)
                    report_worksheet.write(row, 7, list_dict['ticket_remaining_qty'], cell_number)
                    report_worksheet.write(row, 8, list_dict['ticket_created_qty'], cell_number)
                    report_worksheet.write(row, 9, list_dict['qty_delivered'], cell_number)
                    report_worksheet.write(row, 10, list_dict['unloaded_balance_qty'], cell_number)
                    report_worksheet.write(row, 11, list_dict['balance_qty'], cell_number)
                    report_worksheet.write(row, 12, list_dict['qty_invoiced'], cell_amount)
                    report_worksheet.write(row, 13, list_dict['qty_to_invoice'], cell_amount)
                    report_worksheet.write(row, 14, list_dict['price_subtotal'], cell_amount)
                    row += 1
                    total_qty += list_dict['product_uom_qty']
                    balance_qty += list_dict['product_uom_qty']
                last_row  = row
                a1_notation_ref = xl_range(first_row, 4, last_row, 4)
                report_worksheet.write(row, 4, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_qty)
                bal_notation_ref = xl_range(first_row, 11, last_row, 11)
                report_worksheet.write(row, 11, '=SUM(' + bal_notation_ref + ')', cell_total_currency, balance_qty)
            row += 1
        return

