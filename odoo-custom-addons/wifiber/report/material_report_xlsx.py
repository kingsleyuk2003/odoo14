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


class MaterialReport(models.AbstractModel):
    _name = 'report.wifiber.material_report'
    _inherit = 'report.report_xlsx.abstract'

    def _get_data(self, form):
        start_date = form['start_date']
        end_date = form['end_date']
        category_id = form['category_id'][0]
        company_id = form['company_id'][0]

        if not start_date:
            where_start_date = ''
        else:
            where_start_date = "assigned_date >= '%s' AND" % (start_date)

        if not end_date:
            where_end_date = "assigned_date <= '%s'" % datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        else:
            where_end_date = "assigned_date <= '%s'" % (end_date)

        if category_id:
            where_category = "category_id = %s AND" % (category_id)

        if company_id:
            where_company = "ticket_company_id = %s AND" % (company_id)

        sql_statement = """
                SELECT
                  qty,
                  is_requested,
                  assigned_date,
                  requested_datetime,
                  material_request.ticket_id ,
                  res_partner.name as requested_by,
                  kin_ticket.name as ticket_name,
                  product_template.name as product_name,
                  kin_ticket.state ,
                  kin_ticket.description,
                  kin_ticket.ticket_id
                FROM
                  material_request 
                  left JOIN res_users  ON requested_by = res_users.id 
                  left JOIN res_partner ON res_users.partner_id = res_partner.id
                  left JOIN kin_ticket  ON material_request.ticket_id = kin_ticket.id
                  left JOIN product_product ON material_request.product_id = product_product.id
                  LEFT JOIN product_template  ON product_product.id = product_template.id
                WHERE
                    kin_ticket.state != 'cancel' AND  
                    """ + where_category + """  
                     """ + where_company + """
                      """ + where_start_date + """
                       """ + where_end_date + """ 
                ORDER BY
                    requested_datetime desc     
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

        category_id = data['form']['category_id'][0]
        cat_name = self.env['kin.ticket.category'].browse(category_id).name

        # Period
        control_report_worksheet.set_row(0, 20)
        if start_date and end_date:
            start_date_format = localize_tz(datetime.strptime(start_date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(
                user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p')
            end_date_format = localize_tz(datetime.strptime(end_date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(
                user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p')
            control_report_worksheet.merge_range(0, 0, 0, 10,
                                                 '%s %s MATERIAL REQUEST REPORT FROM %s to %s' % (
                                                     user_company.name, cat_name,start_date_format, end_date_format),
                                                 title_format)
        else:
            control_report_worksheet.merge_range(0, 0, 0, 10,
                                                 '%s %s MATERIAL REQUEST REPORT FOR ALL PERIOD' % (user_company.name,cat_name),
                                                 title_format)

        col = 0
        row = 2
        control_report_worksheet.set_column(0, 0, 15)
        control_report_worksheet.set_column(1, 1, 10)
        control_report_worksheet.set_column(2, 2, 30)
        control_report_worksheet.set_column(3, 3, 10)
        control_report_worksheet.set_column(4, 4, 5)
        control_report_worksheet.set_column(5, 5, 15)
        control_report_worksheet.set_column(6, 6, 30)
        control_report_worksheet.set_column(7, 7, 15)
        control_report_worksheet.set_column(8, 8, 10)


        control_report_worksheet.write_row(row, col, (
            'Assigned Date and Time', 'Ticket ID' , 'Title', 'Material' , 'Qty.',  'Requested By', 'Description' , 'Requested Date and Time','Status'), head_format)

        row += 1
        for list_dict in list_dicts:
            control_report_worksheet.write(row, 0,
                                           localize_tz(list_dict['assigned_date'], '%Y-%m-%d %H:%M:%S').astimezone(
                                               user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict[
                                               'assigned_date'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 1, list_dict['ticket_id'], cell_wrap_format)
            control_report_worksheet.write(row, 2, list_dict['ticket_name'], cell_wrap_format)
            control_report_worksheet.write(row, 3, list_dict['product_name'], cell_wrap_format)
            control_report_worksheet.write(row, 4, list_dict['qty'], cell_wrap_format)
            control_report_worksheet.write(row, 5, list_dict['requested_by'], cell_wrap_format)
            control_report_worksheet.write(row, 6, list_dict['description'], cell_wrap_format)
            control_report_worksheet.write(row, 7,
                                           localize_tz(list_dict['requested_datetime'], '%Y-%m-%d %H:%M:%S').astimezone(
                                               user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict[
                                               'requested_datetime'] else '', cell_wrap_format)

            control_report_worksheet.write(row, 8, list_dict['state'], cell_wrap_format)
            row += 1

