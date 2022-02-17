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

class LoadingTicketReport(models.TransientModel):
    _name = 'report.kin_loading.report_stock_picking'
    _inherit = 'report.report_xlsx.abstract'


    def _get_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']
        type = form['type']
        partner_id = form['partner_id']
        product_ids = form['product_ids']
        states = form['states']
        ticket_ids = form['ticket_ids']

        where_states = ''
        if states == 'done' :
            where_states = "AND sp.state = 'done' "
        elif states == 'not_done' :
            where_states = "AND sp.state != 'done' "

        where_start_date = ''
        if start_date :
            where_start_date = "sp.ticket_date >= '%s' AND" % (start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')

        where_type = ''
        if type == 'is_throughput':
            where_type = "sp.is_throughput_ticket = True AND"
        elif type == 'is_internal_use':
            where_type = "sp.is_internal_use_ticket = True AND"
        elif type == 'is_indepot':
            where_type = "sp.is_indepot_ticket = True AND"
        elif type == 'all':
            where_type = ""

        where_partn = ''
        if partner_id :
            where_partn = "sp.partner_id in (%s) AND" % (partner_id[0])

        where_prod = ''
        if product_ids :
            where_prod = "sp.product_id in (%s) AND" % ','.join(str(pr_id) for pr_id in product_ids)

        where_tik = ''
        if ticket_ids:
            where_tik = "sp.id in (%s) AND" % ','.join(str(tk_id) for tk_id in ticket_ids)


        # where_tik = ''
        # if ticket_id:
        #     where_tik = "sp.id = %s AND" % (ticket_id[0])

        # LEFT JOIN works similar to INNER JOIN but with the extra advantage of showing empty join parameter fields (uncompulsory join fields). It is good for join fields that don't have value. It will still show the records. Unlike INNER JOIN (for compulsory join fields) which will omit those records
        sql_statement = """SELECT row_number() over(order by sp.ticket_date) as sn, sp.origin,
                                to_char(sp.create_date,'YYYY-mm-dd HH:MM:SS') as create_date,
                                sp.date_done,
                                sp.ticket_date as ticket_date,
                               sp.partner_id, sp.picking_type_id, sp.location_id,
                               sp.state, sp.name as picking_name, sp.date, sp.location_dest_id,
                               sp.is_block_ticket, sp.is_loading_ticket, sp.truck_no,
                               sp.total_dispatch_qty, sp.ticket_load_qty, sp.is_exdepot_ticket,
                               sp.product_id, sp.picking_type_code,  prod.name as product_name,
                               driver_name, partner.name as partner_name
                          FROM public.stock_picking as sp
                          LEFT JOIN product_template as prod ON sp.product_id = prod.id                        
                          LEFT JOIN res_partner as partner ON sp.partner_id = partner.id
                          WHERE
                          """ + where_start_date +"""
                          """ + where_type +"""
                         """ + where_partn + """
                         """ + where_tik + """
                         """ + where_prod + """
                         sp.ticket_date <= %s
                         """ + where_states + """
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

        product_ids = data['form']['product_ids']
        if not product_ids:
            pro_ids = self.env['product.product'].search([('type', '=', 'product')])
            for pr_id in pro_ids:
                product_ids.append(pr_id.id)

        # stock_dispatch_location_ids = data['form']['stock_dispatch_location_ids']
        # stklocs = ''
        # if stock_dispatch_location_ids :
        #     for operating_unit_id in stock_dispatch_location_ids:
        #         sl_name = self.env['stock.location'].browse(operating_unit_id).name
        #         stklocs +=',' + sl_name
        # else:
        #     stklocs = 'All Depots'

        report_worksheet = workbook.add_worksheet('Loading Ticket Report')
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
        type = data['form']['type']
        if type == 'is_throughput':
            report_worksheet.merge_range(2, 0, 2, 10, 'Throughput Loading Ticket Report' , title_format)
        elif type == 'is_internal_use':
            report_worksheet.merge_range(2, 0, 2, 10, 'Internal Use Loading Ticket Report' , title_format)
        elif type == 'is_indepot':
            report_worksheet.merge_range(2, 0, 2, 10, 'In Depot Loading Ticket Report' , title_format)
        elif type == 'all':
            report_worksheet.merge_range(2, 0, 2, 10, 'All Loading Ticket Report' , title_format)



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
        row = 5
        report_worksheet.set_column(0, 0, 5)
        report_worksheet.set_column(1, 2, 10)
        report_worksheet.set_column(3, 3, 25)
        report_worksheet.set_column(4, 13, 10)

        product_obj = self.env['product.product']
        for product_id in product_ids:
            report_worksheet.set_row(row, 20)
            row += 2
            product_name = product_obj.browse(product_id).name
            report_worksheet.merge_range(row, col, row, 9, product_name, title_format)
            row += 2

            report_worksheet.write_row(row, col, ('S/N', 'Ticket ID', 'Order ID', 'Customer' ,'Ticket Date' , 'Product', 'Qty.', 'Status', 'Loaded Date', 'Vehicle No.','Driver Name', 'Is loading Ticket', 'Is ExDepot Ticket','Picking Operation') , head_format)
            row += 1
            total_qty = 0
            first_row = row
            a1_notation_total_qty_start = xl_rowcol_to_cell(row, 1)
            for list_dict in list_dicts:
                if list_dict['product_id'] == product_id:
                    report_worksheet.write(row, 0, list_dict['sn'],cell_wrap_format)
                    report_worksheet.write(row, 1, list_dict['picking_name'], cell_wrap_format)
                    report_worksheet.write(row, 2, list_dict['origin'], cell_wrap_format)
                    report_worksheet.write(row, 3, list_dict['partner_name'], cell_wrap_format)
                    report_worksheet.write(row, 4, list_dict['ticket_date'] and list_dict['ticket_date'].strftime('%d/%m/%Y'), cell_wrap_format) or False
                    report_worksheet.write(row, 5, list_dict['product_name'], cell_wrap_format)
                    if  list_dict['picking_type_code'] == 'incoming':
                        load_qty =  -list_dict['ticket_load_qty']
                    else:
                        load_qty =  list_dict['ticket_load_qty']
                    report_worksheet.write(row, 6, load_qty, cell_number)
                    if list_dict['state'] == 'done' :
                        str_state = 'Loaded'
                    elif list_dict['state'] == 'cancel' :
                        str_state = 'Cancelled'
                    elif list_dict['is_block_ticket'] :
                        str_state = 'Blocked'
                    elif list_dict['state'] != 'done' :
                        str_state = 'Un-Loaded'
                    else:
                        str_state = 'UnDefined'
                    report_worksheet.write(row, 7, str_state, cell_wrap_format)
                    report_worksheet.write(row, 8, list_dict['date_done'] and list_dict['date_done'].strftime('%d/%m/%Y %H:%M:%S'), cell_wrap_format) or False
                    report_worksheet.write(row, 9, list_dict['truck_no'], cell_wrap_format)
                    report_worksheet.write(row, 10, list_dict['driver_name'], cell_wrap_format)
                    report_worksheet.write(row, 11, list_dict['is_loading_ticket'], cell_wrap_format)
                    report_worksheet.write(row, 12, list_dict['is_exdepot_ticket'], cell_wrap_format)
                    # report_worksheet.write(row, 13, list_dict['is_block_ticket'], cell_wrap_format)
                    report_worksheet.write(row, 13, list_dict['picking_type_code'], cell_wrap_format)
                    row += 1
                    total_qty += float(load_qty)
                last_row  = row
                a1_notation_ref = xl_range(first_row, 6, last_row, 6)
                report_worksheet.write(row, 6, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_qty)
            row += 1
        return

