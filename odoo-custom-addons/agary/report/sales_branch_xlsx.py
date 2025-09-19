# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2025  Kinsolve Solutions
# Copyright 2025 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from odoo import api, fields, models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell

class SalesBranchReport(models.TransientModel):
    _name = 'report.agary.report_sales_branch'
    _inherit = 'report.report_xlsx.abstract'

    def _get_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']
        branch_id = form['branch_id']

        where_start_date = ''
        if start_date :
            where_start_date = "sale_order.date_order >= '%s' AND" % (start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        where_branch = ''
        if branch_id :
            where_branch = "sale_order.branch_id = '%s' AND" % (branch_id[0])


        # LEFT JOIN works similar to INNER JOIN but with the extra advantage of showing empty join parameter fields (uncompulsory join fields). It is good for join fields that don't have value. It will still show the records. Unlike INNER JOIN (for compulsory join fields) which will omit those records
        sql_statement = """
            SELECT row_number() over(order by sale_order.date_order) as sn,
               sol.qty_to_invoice, sol.price_unit, sol.product_uom_qty,
               sol.qty_invoiced, sol.currency_id,
               sol.product_uom, sol.name as prod_name, sol.state, sol.order_partner_id,
               sol.order_id, sol.price_subtotal, sol.discount, sol.price_reduce,
               sol.qty_delivered, sol.price_total, sol.product_id, sol.salesman_id, sale_order.date_order, 
               customer.name as customer_name, sale_order.name as so_name, sales_per_user.name as sales_rep,
               sale_order.client_order_ref,
               sale_order.state
            FROM sale_order_line as sol
            LEFT JOIN res_partner as customer ON sol.order_partner_id = customer.id            
            LEFT JOIN sale_order as sale_order ON sol.order_id = sale_order.id      
            LEFT JOIN res_users as sales_person ON sol.salesman_id = sales_person.id
            LEFT JOIN res_partner as sales_per_user ON sales_person.partner_id = sales_per_user.id      
            WHERE
             """ + where_start_date +"""            
             """ + where_branch +"""   
             sale_order.date_order <= %s AND
              sol.state NOT IN ('draft','cancel')
            """
        args = (end_date,)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()

        return dictAll


    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        list_dicts = self._get_data(data['form'])

        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')

        report_worksheet = workbook.add_worksheet('Sales Rep. Sales Report')
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 24})
        title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        head_format = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10,'bg_color':'blue','color':'white'})
        head_format.set_num_format('#,#00.00')
        head_format_total = workbook.add_format({'bold': True, 'border': 1})
        head_sub_format_indent1 = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        head_sub_format_indent1.set_indent(1)
        cell_total_description = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_wrap_format = workbook.add_format({'valign': 'vjustify', 'font_size': 10, 'border': 1})
        cell_amount = workbook.add_format({'border': 1, 'font_size': 10})
        cell_amount.set_num_format('#,#0.00')
        cell_total_currency = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_total_currency.set_num_format('#,#00.00')
        cell_number = workbook.add_format({'border': 1, 'font_size': 10})
        cell_number.set_num_format('#,#')

        # Header Format
        report_worksheet.set_row(0, 30)  # Set row height
        report_worksheet.merge_range(0, 0, 0, 10, user_company.name, header_format)

        # Title Format
        report_worksheet.set_row(2, 20)

        #Branch
        branch_id = data['form']['branch_id']
        user_name = self.env['res.branch'].browse(branch_id[0]).name
        report_worksheet.merge_range(2, 0, 2, 10, user_name + ' Branch Report' , title_format)


        # Period
        report_worksheet.set_row(3, 20)
        if start_date and end_date:
            report_worksheet.merge_range(3, 0, 3, 10,
                                         'Period: ' + datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S').strftime(
                                             '%d/%m/%Y') + '  to ' + datetime.strptime(end_date,
                                                                                       '%Y-%m-%d %H:%M:%S').strftime(
                                             '%d/%m/%Y'), title_format)
        else:
            report_worksheet.merge_range(3, 0, 3, 10, 'Period: All', title_format)

        col = 0
        row = 7
        report_worksheet.set_column(0, 0, 5)
        report_worksheet.set_column(1, 2, 10)
        report_worksheet.set_column(3, 3, 25)
        report_worksheet.set_column(4, 23, 10)

        report_worksheet.write_row(row, col,
                                   ('S/N', 'Order ID', 'Order Date', 'Sales Representative','Customer', 'PO Ref.', 'Product', 'Ordered Qty.',
                                    'Delivered Qty.', 'Invoiced', 'Un-Invoiced', 'Unit Price', 'Disc(%)', 'Sub-total',
                                    'Status'), head_format)
        row += 1
        first_row = row
        total_qty = total_product_uom_qty = total_qty_delivered = total_qty_invoiced = total_qty_to_invoice = 0
        for list_dict in list_dicts:
            report_worksheet.write(row, 0, list_dict['sn'], cell_wrap_format)
            report_worksheet.write(row, 1, list_dict['so_name'], cell_wrap_format)
            report_worksheet.write(row, 2, list_dict['date_order'].strftime('%d/%m/%Y %H:%M:%S'), cell_wrap_format)
            report_worksheet.write(row, 3, list_dict['sales_rep'], cell_wrap_format)
            report_worksheet.write(row, 4, list_dict['customer_name'], cell_wrap_format)
            report_worksheet.write(row, 5, list_dict['client_order_ref'], cell_wrap_format)
            report_worksheet.write(row, 6, list_dict['prod_name'], cell_wrap_format)
            report_worksheet.write(row, 7, list_dict['product_uom_qty'], cell_number)
            report_worksheet.write(row, 8, list_dict['qty_delivered'], cell_number)
            report_worksheet.write(row, 9, list_dict['qty_invoiced'], cell_number)
            report_worksheet.write(row, 10, list_dict['qty_to_invoice'], cell_number)
            report_worksheet.write(row, 11, list_dict['price_unit'], cell_amount)
            report_worksheet.write(row, 12, list_dict['discount'], cell_amount)
            report_worksheet.write(row, 13, list_dict['price_subtotal'], cell_amount)
            report_worksheet.write(row, 14, list_dict['state'], cell_wrap_format)
            row += 1
            total_product_uom_qty += list_dict['product_uom_qty']
            total_qty_delivered += list_dict['qty_delivered']
            total_qty_invoiced += list_dict['qty_invoiced']
            total_qty_to_invoice += list_dict['qty_to_invoice']
            total_qty += list_dict['price_subtotal']
        last_row = row
        notation_ref = xl_range(first_row, 7, last_row, 7)
        report_worksheet.write(row, 7, '=SUM(' + notation_ref + ')', cell_total_currency, total_product_uom_qty)
        notation_ref = xl_range(first_row, 8, last_row, 8)
        report_worksheet.write(row, 8, '=SUM(' + notation_ref + ')', cell_total_currency, total_qty_delivered)
        notation_ref = xl_range(first_row, 9, last_row, 9)
        report_worksheet.write(row, 9, '=SUM(' + notation_ref + ')', cell_total_currency, total_qty_invoiced)
        notation_ref = xl_range(first_row, 10, last_row, 10)
        report_worksheet.write(row, 10, '=SUM(' + notation_ref + ')', cell_total_currency, total_qty_to_invoice)
        notation_ref = xl_range(first_row, 13, last_row, 13)
        report_worksheet.write(row, 13, '=SUM(' + notation_ref + ')', cell_total_currency, total_qty)
        return

