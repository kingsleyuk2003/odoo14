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


class IssuedReport(models.AbstractModel):
    _name = 'report.wifiber.issued_report'
    _inherit = 'report.report_xlsx.abstract'

    def _get_data(self, form):
        start_date = form['start_date']
        end_date = form['end_date']
        company_id = form['company_id'][0]

        if not start_date:
            where_start_date = ''
        else:
            where_start_date = "assigned_date >= '%s' AND" % (start_date)

        if not end_date:
            where_end_date = "assigned_date <= '%s'" % datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        else:
            where_end_date = "assigned_date <= '%s'" % (end_date)

        if company_id:
            where_company = "ticket_company_id = %s AND" % (company_id)

        sql_statement = """
                SELECT   
                  assigned_date,  
                  issuedby.name as issued_by,
                  issued_datetime,  
                  qty_done,     
                  stock_production_lot.name lot_name,
                  stock_move_line.date,
                  from_loc.name as from_location,
                  dest_loc.name as dest_location,
                  stock_move_line.state,
                  reference ,    
                  kin_ticket.name as ticket_name,
                  product_template.name as product_name,
                  kin_ticket.state as ticket_state ,
                  kin_ticket.description,
                  kin_ticket.ticket_id,
                  pt.name as plan,
                  partner_id.name as partner_name,
                  partner_id.ref,
                  partner_id.mobile,
                  partner_id.phone,
                  partner_id.email
                FROM
                  stock_move_line 
                  left JOIN product_product ON stock_move_line.product_id = product_product.id
                  LEFT JOIN product_template  ON product_product.id = product_template.id
                  left JOIN stock_location as from_loc  ON stock_move_line.location_id = from_loc.id 
                  left JOIN stock_location as dest_loc  ON location_dest_id = dest_loc.id 
                  left JOIN kin_ticket  ON stock_move_line.ticket_id = kin_ticket.id  
                  left Join res_partner as partner_id ON kin_ticket.partner_id = partner_id.id   
                  left JOIN product_product tp ON partner_id.product_id = tp.id
                  LEFT JOIN product_template as pt  ON tp.id = pt.id             
                  left JOIN res_users  ON stock_move_line.issued_by = res_users.id                   
                  left JOIN res_partner issuedby ON res_users.partner_id = issuedby.id 
                  left JOIN stock_production_lot ON stock_move_line.lot_id = stock_production_lot.id
                WHERE
                    stock_move_line.state = 'done' AND   
                     """ + where_company + """
                      """ + where_start_date + """
                       """ + where_end_date + """ 
                ORDER BY
                    issued_datetime desc     
            """
        self.env.cr.execute(sql_statement)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        list_dicts = self._get_data(data['form'])

        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        user_tz_obj = pytz.timezone(self.env.context.get('tz') or 'utc')
        localize_tz = pytz.utc.localize

        control_report_worksheet = workbook.add_worksheet('Material Requested Ticket Report')
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 24})
        title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
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

        # Header Format
        control_report_worksheet.set_row(0, 30)  # Set row height
        # control_report_worksheet.merge_range(0, 0, 0, 10, user_company.name, header_format)

        # Title Format
        control_report_worksheet.set_row(2, 20)
        # control_report_worksheet.merge_range(2, 0, 2, 10, 'Report', title_format)


        # Period
        control_report_worksheet.set_row(0, 20)
        if start_date and end_date:
            start_date_format = localize_tz(datetime.strptime(start_date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(
                user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p')
            end_date_format = localize_tz(datetime.strptime(end_date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(
                user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p')
            control_report_worksheet.merge_range(0, 0, 0, 10,
                                                 '%s MATERIAL ISSUED (USED) REPORT FROM %s to %s' % (
                                                     user_company.name, start_date_format, end_date_format),
                                                 title_format)
        else:
            control_report_worksheet.merge_range(0, 0, 0, 10,
                                                 '%s MATERIAL ISSUED (USED) REPORT FOR ALL PERIOD' % (user_company.name),
                                                 title_format)

        col = 0
        row = 2
        control_report_worksheet.set_column(0, 0, 15)
        control_report_worksheet.set_column(1, 1, 10)
        control_report_worksheet.set_column(2, 2, 30)
        control_report_worksheet.set_column(3, 3, 10)
        control_report_worksheet.set_column(4, 4, 10)
        control_report_worksheet.set_column(5, 5, 10)
        control_report_worksheet.set_column(6, 6, 10)
        control_report_worksheet.set_column(7, 7, 5)
        control_report_worksheet.set_column(8, 8, 10)
        control_report_worksheet.set_column(9, 9, 10)
        control_report_worksheet.set_column(10, 10, 10)
        control_report_worksheet.set_column(11, 11, 10)
        control_report_worksheet.set_column(12, 12, 10)
        control_report_worksheet.set_column(13, 13, 30)
        control_report_worksheet.set_column(14, 14, 10)
        control_report_worksheet.set_column(15, 15, 15)
        control_report_worksheet.set_column(16, 16, 10)
        control_report_worksheet.set_column(17, 17, 10)
        control_report_worksheet.set_column(18, 18, 10)
        control_report_worksheet.set_column(19, 19, 10)
        control_report_worksheet.set_column(20, 20, 10)


        control_report_worksheet.write_row(row, col, (
            'Assigned Date and Time', 'Ticket ID' , 'Title', 'Material' , 'From Location' , 'To Location', 'Serial No.' , 'Qty. Done' ,'Issued By', 'Issued Date and Time' , 'Stock Move Date and Time' , 'Stock Move Status' , 'Stock Picking ID' , 'Ticket Description','Service Plan' , 'Customer' , 'Client ID' , 'Mobile','Phone' , 'Email', 'Ticket Status'), head_format)

        row += 1
        for list_dict in list_dicts:
            control_report_worksheet.write(row, 0,
                                           localize_tz(list_dict['assigned_date'], '%Y-%m-%d %H:%M:%S').astimezone(
                                               user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict[
                                               'assigned_date'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 1, list_dict['ticket_id'], cell_wrap_format)
            control_report_worksheet.write(row, 2, list_dict['ticket_name'], cell_wrap_format)
            control_report_worksheet.write(row, 3, list_dict['product_name'], cell_wrap_format)
            control_report_worksheet.write(row, 4, list_dict['from_location'], cell_wrap_format)
            control_report_worksheet.write(row, 5, list_dict['dest_location'], cell_wrap_format)
            control_report_worksheet.write(row, 6, list_dict['lot_name'], cell_wrap_format)
            control_report_worksheet.write(row, 7, list_dict['qty_done'], cell_wrap_format)
            control_report_worksheet.write(row, 8, list_dict['issued_by'], cell_wrap_format)
            control_report_worksheet.write(row, 9,
                                           localize_tz(list_dict['issued_datetime'], '%Y-%m-%d %H:%M:%S').astimezone(
                                               user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict[
                                               'issued_datetime'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 10,
                                           localize_tz(list_dict['date'], '%Y-%m-%d %H:%M:%S').astimezone(
                                               user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict[
                                               'date'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 11, list_dict['state'], cell_wrap_format)
            control_report_worksheet.write(row, 12, list_dict['reference'], cell_wrap_format)
            control_report_worksheet.write(row, 13, list_dict['description'], cell_wrap_format)
            control_report_worksheet.write(row, 14, list_dict['plan'], cell_wrap_format)
            control_report_worksheet.write(row, 15, list_dict['partner_name'], cell_wrap_format)
            control_report_worksheet.write(row, 16, list_dict['ref'], cell_wrap_format)
            control_report_worksheet.write(row, 17, list_dict['mobile'], cell_wrap_format)
            control_report_worksheet.write(row, 18, list_dict['phone'], cell_wrap_format)
            control_report_worksheet.write(row, 19, list_dict['email'], cell_wrap_format)
            control_report_worksheet.write(row, 20, list_dict['ticket_state'], cell_wrap_format)
            row += 1


