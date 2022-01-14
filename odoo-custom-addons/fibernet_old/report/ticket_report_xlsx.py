# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2020  Kinsolve Solutions
# Copyright 2020 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsxAbstract
# from odoo.report import report_sxw
from odoo import models
from datetime import datetime
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from odoo.report import report_sxw
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz


class TicketReport(ReportXlsx):

    def _get_data(self, form):
        start_date = form.start_date
        end_date = form.end_date
        category_id = form['category_id'][0].id
        company_id = form['company_id'][0].id

        if not start_date:
            where_start_date = ''
            where_start_log_date = ''
        else:
            where_start_date = "assigned_date >= '%s' AND" % (start_date)
            where_start_log_date = "last_log_datetime >= '%s' AND" % (start_date)

        if not end_date:
            where_end_date = "assigned_date <= '%s'" % datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            where_end_log_date = "last_log_datetime <= '%s'" % datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        else:
            where_end_date = "assigned_date <= '%s'" % (end_date)
            where_end_log_date = "last_log_datetime <= '%s'" % (end_date)

        if category_id:
            where_category = "category_id = %s AND" % (category_id)

        if company_id:
            where_company = "ticket_company_id = %s AND" % (company_id)

        sql_statement = """

        ( SELECT
                  assigned_date,
                  kin_ticket.name as name,
                  U1.id as user_name_id,
                  user_ticket_group_id,
                  U2.id as assigned_user_name_id,
                  open_date,
                  done_ticket_date,
                  closed_date,
                  time_spent,
                  state,
                  description,
                  non_cust_name,
                  kin_ticket.partner_id as partner_id,
                  non_cust_client_id,                  
                  root_cause,  
                  complaint_type_id,
                  complaint_type_support_id,
                  source_support,
                  source_call,
                  region_call_id,
                  area_customer_id,
                  non_cust_address,
                  non_cust_phone,
                  non_cust_email ,
                  comment_call_log ,
                  last_log_datetime,
                  last_log_user_id,
                  last_log_message            
                FROM
                  kin_ticket
                  left JOIN res_users as U1 ON user_id = U1.id 
                WHERE
                    state != 'cancel' AND                   
                    """ + where_category + """ 
                     """ + where_company + """
                      """ + where_start_date + """
                       """ + where_end_date + """ 
                ORDER BY
                    assigned_date desc

                    ) 

                UNION

                (               
                SELECT
                  assigned_date,
                  kin_ticket.name as name,
                  U1.id as user_name_id,
                  user_ticket_group_id,
                  U2.id as assigned_user_name_id,
                  open_date,
                  done_ticket_date,
                  closed_date,
                  time_spent,
                  state,
                  description,
                  non_cust_name,
                  kin_ticket.partner_id as partner_id,
                  non_cust_client_id,
                  root_cause,  
                  complaint_type_id,
                  complaint_type_support_id,
                  source_support,
                  source_call,
                  region_call_id,
                  area_customer_id,
                  non_cust_address,
                  non_cust_phone,
                  non_cust_email ,
                  comment_call_log ,    
                  last_log_datetime,
                  last_log_user_id,
                  last_log_message         
                FROM
                  kin_ticket
                  left JOIN res_users as U1 ON user_id = U1.id 
                WHERE
                    state != 'cancel' AND                   
                    """ + where_category + """ 
                     """ + where_company + """
                       """ + where_start_log_date + """
                      """ + where_end_log_date + """
                ORDER BY
                    assigned_date desc        
                    )



            """
        self.env.cr.execute(sql_statement)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        list_dicts = self._get_data(objects)

        start_date = objects.start_date
        end_date = objects.end_date
        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        user_tz_obj = pytz.timezone(self.env.context.get('tz') or 'utc')
        localize_tz = pytz.utc.localize

        control_report_worksheet = workbook.add_worksheet('Ticket Report')
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

        cat_name = objects.category_id.name
        # Period
        control_report_worksheet.set_row(0, 20)
        if start_date and end_date:
            start_date_format = localize_tz(datetime.strptime(start_date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p')
            end_date_format = localize_tz(datetime.strptime(end_date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p')
            control_report_worksheet.merge_range(0, 0, 0, 10,
                                                 '%s %s REPORT FROM %s to %s' % (
                                                 user_company.name, cat_name, start_date_format, end_date_format),
                                                 title_format)
        else:
            control_report_worksheet.merge_range(0, 0, 0, 10,
                                                 '%s %s REPORT FOR ALL PERIOD' % (user_company.name, cat_name),
                                                 title_format)

        col = 0
        row = 2
        control_report_worksheet.set_column(0, 0, 15)
        control_report_worksheet.set_column(1, 1, 30)
        control_report_worksheet.set_column(2, 2, 15)
        control_report_worksheet.set_column(3, 3, 15)
        control_report_worksheet.set_column(4, 4, 15)
        control_report_worksheet.set_column(5, 5, 15)
        control_report_worksheet.set_column(6, 6, 15)
        control_report_worksheet.set_column(7, 7, 15)
        control_report_worksheet.set_column(8, 8, 15)
        control_report_worksheet.set_column(9, 9, 10)
        control_report_worksheet.set_column(10, 10, 30)
        control_report_worksheet.set_column(11, 11, 15)

        control_report_worksheet.set_column(12, 12, 15)
        control_report_worksheet.set_column(13, 13, 15)
        control_report_worksheet.set_column(14, 14, 15)
        control_report_worksheet.set_column(15, 15, 15)
        control_report_worksheet.set_column(16, 16, 15)

        control_report_worksheet.set_column(17, 17, 15)
        control_report_worksheet.set_column(18, 18, 15)
        control_report_worksheet.set_column(19, 19, 15)
        control_report_worksheet.set_column(20, 20, 15)
        control_report_worksheet.set_column(21, 21, 15)

        control_report_worksheet.set_column(22, 22, 15)
        control_report_worksheet.set_column(23, 23, 15)
        control_report_worksheet.set_column(24, 24, 15)
        control_report_worksheet.set_column(25, 25, 15)
        control_report_worksheet.set_column(26, 26, 15)
        control_report_worksheet.set_column(27, 27, 15)
        control_report_worksheet.set_column(28, 28, 15)
        control_report_worksheet.set_column(29, 29, 15)
        control_report_worksheet.set_column(30, 30, 30)

        control_report_worksheet.set_column(31, 31, 15)
        control_report_worksheet.set_column(32, 32, 15)
        control_report_worksheet.set_column(33, 33, 30)

        control_report_worksheet.write_row(row, col, (
        'Assigned Date and Time', 'Title', 'Ticket Opener', 'Assigned User', 'User Ticket Group',
        'Opened Date and Time', 'Done Date and Time', 'Closed Date and Time', 'Time Spent', 'Stage', 'Incident Details',
        'Package', 'Customer', 'Client ID', 'Address', 'Phone', 'Mobile' ,'Email', 'Non Customer Name', 'Non-Customer Client ID',
        ' Non-Customer Address', 'Non-Customer Phone', 'Non-Customer Email', 'Root Cause', 'Region', 'Area',
        'Call log Complaint Type', 'Support Complaint Type', 'Source Support', 'Source Call Log', 'Call Log Comment/Feedback',
        'Last Logged Datetime', 'Last Logged User', 'Last Log Message'), head_format)

        res_user_obj = self.env['res.users']
        user_ticket_group_obj = self.env['user.ticket.group']
        region_obj = self.env['kkon.region']
        area_obj = self.env['kkon.area']
        complaint_type_obj = self.env['kkon.complaint.type']
        res_partner_obj = self.env['res.partner']

        row += 1
        first_row = row
        for list_dict in list_dicts:
            control_report_worksheet.write(row, 0, localize_tz(datetime.strptime(list_dict['assigned_date'], '%Y-%m-%d %H:%M:%S')).astimezone(user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict['assigned_date'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 1, list_dict['name'], cell_wrap_format)
            control_report_worksheet.write(row, 2, res_user_obj.browse(list_dict['user_name_id']).name, cell_wrap_format)
            control_report_worksheet.write(row, 3, res_user_obj.browse(list_dict['assigned_user_name_id']).name or '',cell_wrap_format)
            control_report_worksheet.write(row, 4, user_ticket_group_obj.sudo().browse(list_dict['user_ticket_group_id']).name or '', cell_wrap_format)
            control_report_worksheet.write(row, 5, localize_tz(datetime.strptime(list_dict['open_date'], '%Y-%m-%d %H:%M:%S')).astimezone(user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict['open_date'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 6, localize_tz(datetime.strptime(list_dict['done_ticket_date'],'%Y-%m-%d %H:%M:%S')).astimezone(user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict['done_ticket_date'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 7, (localize_tz(datetime.strptime(list_dict['closed_date'], '%Y-%m-%d %H:%M:%S')).astimezone(user_tz_obj).strftime('%d/%m/%Y %H:%%I:%M:%S %p:%S') if list_dict['closed_date'] else ''), cell_wrap_format)
            control_report_worksheet.write(row, 8, list_dict['time_spent'], cell_wrap_format)
            control_report_worksheet.write(row, 9, list_dict['state'], cell_wrap_format)
            control_report_worksheet.write(row, 10, list_dict['description'], cell_wrap_format)
            control_report_worksheet.write(row, 11, res_partner_obj.sudo().browse(list_dict['partner_id']).product_id.name or '', cell_wrap_format)

            control_report_worksheet.write(row, 12, res_partner_obj.sudo().browse(list_dict['partner_id']).name or '',cell_wrap_format)
            control_report_worksheet.write(row, 13, res_partner_obj.sudo().browse(list_dict['partner_id']).ref or '',cell_wrap_format)
            control_report_worksheet.write(row, 14, res_partner_obj.sudo().browse(list_dict['partner_id']).street or '',cell_wrap_format)
            control_report_worksheet.write(row, 15, res_partner_obj.sudo().browse(list_dict['partner_id']).phone or '',cell_wrap_format)
            control_report_worksheet.write(row, 16, res_partner_obj.sudo().browse(list_dict['partner_id']).mobile or '', cell_wrap_format)
            control_report_worksheet.write(row, 17, res_partner_obj.sudo().browse(list_dict['partner_id']).email or '',cell_wrap_format)

            control_report_worksheet.write(row, 18, list_dict['non_cust_name'], cell_wrap_format)
            control_report_worksheet.write(row, 19, list_dict['non_cust_client_id'], cell_wrap_format)
            control_report_worksheet.write(row, 20, list_dict['non_cust_address'], cell_wrap_format)
            control_report_worksheet.write(row, 21, list_dict['non_cust_phone'], cell_wrap_format)
            control_report_worksheet.write(row, 22, list_dict['non_cust_email'], cell_wrap_format)

            control_report_worksheet.write(row, 23, list_dict['root_cause'], cell_wrap_format)
            control_report_worksheet.write(row, 24, region_obj.sudo().browse(list_dict['region_call_id']).name or '',cell_wrap_format)
            control_report_worksheet.write(row, 25, area_obj.sudo().browse(list_dict['area_customer_id']).name or '',cell_wrap_format)
            control_report_worksheet.write(row, 26,complaint_type_obj.sudo().browse(list_dict['complaint_type_id']).name or '', cell_wrap_format)
            control_report_worksheet.write(row, 27, complaint_type_obj.sudo().browse(list_dict['complaint_type_support_id']).name or '', cell_wrap_format)
            control_report_worksheet.write(row, 28, list_dict['source_support'], cell_wrap_format)
            control_report_worksheet.write(row, 29, list_dict['source_call'], cell_wrap_format)
            control_report_worksheet.write(row, 30, list_dict['comment_call_log'], cell_wrap_format)

            control_report_worksheet.write(row, 31, localize_tz(datetime.strptime(list_dict['last_log_datetime'], '%Y-%m-%d %H:%M:%S')).astimezone(user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict['last_log_datetime'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 32, res_user_obj.browse(list_dict['last_log_user_id']).name or '',cell_wrap_format)
            control_report_worksheet.write(row, 33, list_dict['last_log_message'], cell_wrap_format)
            row += 1


# The purchase.report.wizard in the PurchaseReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
TicketReport('report.kkon_modifications.ticket_report', 'ticket.wizard', parser=report_sxw.rml_parse)


