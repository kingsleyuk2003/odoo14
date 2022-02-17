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

class SalesReport(models.TransientModel):
    _name = 'report.kin_loading.report_sales_loading_report'
    _inherit = 'report.report_xlsx.abstract'

    def _get_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']
        type = form['type']
        partner_id = form['partner_id']
        partner_root_id = form['partner_root_id']
        include_root_customer_order = form['include_root_customer_order']
        root_order_transfer_id = form['root_order_transfer_id']
        parent_sales_order_transfer_id = form['parent_sales_order_transfer_id']
        product_ids = form['product_ids']

        where_start_date = ''
        if start_date :
            where_start_date = "sale_order.date_order >= '%s' AND" % (start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')

        where_type = ''
        if type == 'is_throughput' :
            where_type = "sol.is_throughput_order = True AND"
        elif type == 'is_internal_use' :
            where_type = "sol.is_internal_use_order = True AND"
        elif type == 'is_indepot' :
            where_type = "sol.is_throughput_order = False AND sol.is_internal_use_order = False AND"
        elif type == 'all' :
            where_type = ""

        where_partner = ''
        if partner_id :
            where_partner = "sol.order_partner_id = '%s' AND" % (partner_id[0])


        where_partner_root = ''
        if partner_root_id :
            where_partner_root = "sol.root_customer_id = '%s' AND" % (partner_root_id[0])

        if include_root_customer_order:
            if not partner_root_id :
                raise UserError('Please Select the Root Customer')
            where_partner = "sol.order_partner_id = '%s' OR" % (partner_root_id[0])

        where_root_order = ''
        if root_order_transfer_id:
            where_root_order = "sol.root_order_transfer_id = '%s' AND" % (root_order_transfer_id[0])

        where_parent_order = ''
        if parent_sales_order_transfer_id:
            where_parent_order = "sol.parent_sales_order_transfer_id = '%s' AND" % (parent_sales_order_transfer_id[0])

        where_prod = ''
        if product_ids:
            where_prod = "sol.product_id in (%s) AND" % ','.join(str(pr_id) for pr_id in product_ids)

        # LEFT JOIN works similar to INNER JOIN but with the extra advantage of showing empty join parameter fields (uncompulsory join fields). It is good for join fields that don't have value. It will still show the records. Unlike INNER JOIN (for compulsory join fields) which will omit those records
        sql_statement = """
            SELECT row_number() over(order by sale_order.date_order) as sn,
               sol.qty_to_invoice, sol.price_unit, sol.product_uom_qty,
               sol.qty_invoiced, sol.currency_id,
               sol.product_uom, sol.name as prod_name, sol.state, sol.order_partner_id,
               sol.order_id, sol.price_subtotal, sol.discount, sol.price_reduce,
               sol.qty_delivered, sol.price_total, sol.product_id, sol.salesman_id, sale_order.date_order, sol.product_ticket_qty, sol.ticket_remaining_qty,
               sol.ticket_created_qty, sol.transfer_created_qty, sol.cancelled_remaining_qty,
               sol.unloaded_balance_qty, sol.balance_qty, sol.parent_sales_order_transfer_id,
               sol.root_order_transfer_id, customer.name as customer_name,
               root_sale_order.name as root_sale_order_name, sale_order.name as so_name,
               sale_order.client_order_ref, parent_sale_order.name as parent_order_name,
               sale_order.state,
               parent_customer.name as parent_customer_name,
               root_customer.name as root_customer_name
            FROM sale_order_line as sol
            LEFT JOIN res_partner as customer ON sol.order_partner_id = customer.id
            LEFT JOIN res_partner as root_customer ON sol.root_customer_id = root_customer.id
            LEFT JOIN sale_order as root_sale_order ON sol.root_order_transfer_id = root_sale_order.id
            LEFT JOIN sale_order as parent_sale_order ON sol.parent_sales_order_transfer_id = parent_sale_order.id
            LEFT JOIN res_partner as parent_customer ON parent_sale_order.partner_id = parent_customer.id
            LEFT JOIN sale_order as sale_order ON sol.order_id = sale_order.id
            WHERE
             """ + where_start_date +"""
             """ + where_type +"""
             """ + where_partner +"""
             """ + where_partner_root +"""
             """ + where_root_order +"""
              """ + where_parent_order +"""
             """ + where_prod + """
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

        product_ids = data['form']['product_ids']
        if not product_ids :
            pro_ids = self.env['product.product'].search([('type','=','product')])
            for pr_id in pro_ids:
                product_ids.append(pr_id.id)

        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')


        report_worksheet = workbook.add_worksheet('Sales Report')
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

        type = data['form']['type']
        if type == 'is_throughput':
            report_worksheet.merge_range(2, 0, 2, 10, 'Throughput Sales Report', title_format)
        elif type == 'is_internal_use':
            report_worksheet.merge_range(2, 0, 2, 10, 'Internal Use Sales Report', title_format)
        elif type == 'is_indepot':
            report_worksheet.merge_range(2, 0, 2, 10, 'In Depot Sales Report', title_format)
        elif type == 'all':
            report_worksheet.merge_range(2, 0, 2, 10, 'All Sales Report', title_format)

        # Period
        report_worksheet.set_row(3, 20)
        if start_date and end_date:
            report_worksheet.merge_range(3, 0, 3, 10,
                                          'Period: ' + datetime.strptime(start_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y') + '  to ' + datetime.strptime(end_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y'), title_format)
        else:
            report_worksheet.merge_range(3, 0, 3, 10, 'Period: All', title_format)

        col = 0
        row = 3
        report_worksheet.set_column(0, 0, 5)
        report_worksheet.set_column(1, 2, 10)
        report_worksheet.set_column(3, 3, 25)
        report_worksheet.set_column(4, 23, 10)

        product_obj =  self.env['product.product']
        for product_id in product_ids :
            report_worksheet.set_row(row, 20)
            row += 2
            product_name = product_obj.browse(product_id).name
            report_worksheet.merge_range(row, col, row, 9, product_name, title_format)
            row += 2

            report_worksheet.write_row(row, col, ('S/N', 'Order ID' , 'Order Date', 'Customer', 'PO Ref.' ,'Parent Transfer Order' ,'Parent Transfer Customer', 'Root Transfer Order', 'Root Transfer Customer', 'Product', 'Ordered Qty.', 'Transferred Qty.', 'Cancelled Qty.', 'Un-Ticketed Qty.' , 'Ticketed Qty.', 'Loaded Qty.', 'Un-loaded Qty.', 'Balance Qty.', 'Invoiced', 'Un-Invoiced' ,'Unit Price' ,'Disc(%)','Sub-total', 'Status' ) , head_format)
            row += 1
            total_qty = 0
            first_row = row
            a1_notation_total_qty_start = xl_rowcol_to_cell(row, 1)
            for list_dict in list_dicts:
                if list_dict['product_id'] == product_id :
                    report_worksheet.write(row, 0, list_dict['sn'],cell_wrap_format)
                    report_worksheet.write(row, 1, list_dict['so_name'], cell_wrap_format)
                    report_worksheet.write(row, 2, list_dict['date_order'].strftime('%d/%m/%Y %H:%M:%S'), cell_wrap_format)
                    report_worksheet.write(row, 3, list_dict['customer_name'], cell_wrap_format)
                    report_worksheet.write(row, 4, list_dict['client_order_ref'], cell_wrap_format)
                    report_worksheet.write(row, 5, list_dict['parent_order_name'], cell_wrap_format)
                    report_worksheet.write(row, 6, list_dict['parent_customer_name'], cell_wrap_format)
                    report_worksheet.write(row, 7, list_dict['root_sale_order_name'], cell_wrap_format)
                    report_worksheet.write(row, 8, list_dict['root_customer_name'], cell_wrap_format)
                    report_worksheet.write(row, 9, list_dict['prod_name'], cell_wrap_format)
                    report_worksheet.write(row, 10, list_dict['product_uom_qty'], cell_number)
                    report_worksheet.write(row, 11, list_dict['transfer_created_qty'], cell_number)
                    report_worksheet.write(row, 12, list_dict['cancelled_remaining_qty'], cell_number)
                    report_worksheet.write(row, 13, list_dict['ticket_remaining_qty'], cell_number)
                    report_worksheet.write(row, 14, list_dict['ticket_created_qty'], cell_number)
                    report_worksheet.write(row, 15, list_dict['qty_delivered'], cell_number)
                    report_worksheet.write(row, 16, list_dict['unloaded_balance_qty'], cell_number)
                    report_worksheet.write(row, 17, list_dict['balance_qty'], cell_number)
                    report_worksheet.write(row, 18, list_dict['qty_invoiced'], cell_number)
                    report_worksheet.write(row, 19, list_dict['qty_to_invoice'], cell_number)
                    report_worksheet.write(row, 20, list_dict['price_unit'], cell_amount)
                    report_worksheet.write(row, 21, list_dict['discount'], cell_amount)
                    report_worksheet.write(row, 22, list_dict['price_subtotal'], cell_amount)
                    report_worksheet.write(row, 23, list_dict['state'], cell_wrap_format)
                    row += 1
                    total_qty += list_dict['balance_qty']
                last_row  = row
                a1_notation_ref = xl_range(first_row, 17, last_row, 17)
                report_worksheet.write(row, 17, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_qty)
            row += 1
        return

