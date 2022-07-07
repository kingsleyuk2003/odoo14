# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2021  Kinsolve Solutions
# Copyright 2021 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from odoo import api, fields, models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell


class TicketReport(models.AbstractModel):
    _name = 'report.fibernet.ticket_report'
    _inherit = 'report.report_xlsx.abstract'


    def _get_data(self, form):
        start_date = form['start_date']
        end_date = form['end_date']
        category_id = form['category_id'][0]
        company_id = form['company_id'][0]

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
                  open_date,
                  done_ticket_date,
                  closed_date,
                  time_spent,
                  state,
                  description,
                  kin_ticket.partner_id as partner_id,            
                  root_cause,  
                  complaint_type_support_id,
                  source_support,
                  prospect_name,
                  prospect_address,
                  prospect_area_id,
                  prospect_phone,
                  prospect_email ,
                 
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
                  open_date,
                  done_ticket_date,
                  closed_date,
                  time_spent,
                  state,
                  description,
                  kin_ticket.partner_id as partner_id,
                  root_cause,  
                  complaint_type_support_id,
                  source_support,
                  prospect_name,
                  prospect_address,
                  prospect_area_id,
                  prospect_phone,
                  prospect_email ,
                    
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
        list_dicts = self._get_data(data['form'])

        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
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

        control_report_worksheet.write_row(row, col, (
        'Assigned Date and Time', 'Title', 'Ticket Opener',  'User Ticket Group',
        'Opened Date and Time', 'Done Date and Time', 'Closed Date and Time', 'Time Spent', 'Stage', 'Incident Details',
        'Package', 'Customer', 'Client ID', 'Address', 'Phone', 'Mobile' ,'Email', 'Prospect Name', 'Prospect Area',
        'Prospect Address', 'Prospect Phone', 'Prospect Email', 'Root Cause',  'Support Complaint Type', 'Source Support',
        'Last Logged Datetime', 'Last Logged User', 'Last Log Message'), head_format)

        res_user_obj = self.env['res.users']
        user_ticket_group_obj = self.env['user.ticket.group']
        region_obj = self.env['region']
        area_obj = self.env['area']
        complaint_type_obj = self.env['complaint.type']
        res_partner_obj = self.env['res.partner']
        prospect_area_obj = self.env['area']

        row += 1
        first_row = row
        for list_dict in list_dicts:
            control_report_worksheet.write(row, 0, localize_tz(list_dict['assigned_date'], '%Y-%m-%d %H:%M:%S').astimezone(user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict['assigned_date'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 1, list_dict['name'], cell_wrap_format)
            control_report_worksheet.write(row, 2, res_user_obj.browse(list_dict['user_name_id']).name, cell_wrap_format)

            control_report_worksheet.write(row, 3, user_ticket_group_obj.sudo().browse(list_dict['user_ticket_group_id']).name or '', cell_wrap_format)
            control_report_worksheet.write(row, 4, localize_tz(datetime.strptime(str(list_dict['open_date']), '%Y-%m-%d %H:%M:%S')).astimezone(user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict['open_date'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 5, localize_tz(datetime.strptime(str(list_dict['done_ticket_date']),'%Y-%m-%d %H:%M:%S')).astimezone(user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict['done_ticket_date'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 6, (localize_tz(datetime.strptime(str(list_dict['closed_date']), '%Y-%m-%d %H:%M:%S')).astimezone(user_tz_obj).strftime('%d/%m/%Y %H:%%I:%M:%S %p:%S') if list_dict['closed_date'] else ''), cell_wrap_format)
            control_report_worksheet.write(row, 7, list_dict['time_spent'], cell_wrap_format)
            control_report_worksheet.write(row, 8, list_dict['state'], cell_wrap_format)
            control_report_worksheet.write(row, 9, list_dict['description'], cell_wrap_format)
            control_report_worksheet.write(row, 10, res_partner_obj.sudo().browse(list_dict['partner_id']).product_id.name or '', cell_wrap_format)

            control_report_worksheet.write(row, 11, res_partner_obj.sudo().browse(list_dict['partner_id']).name or '',cell_wrap_format)
            control_report_worksheet.write(row, 12, res_partner_obj.sudo().browse(list_dict['partner_id']).ref or '',cell_wrap_format)
            control_report_worksheet.write(row, 13, res_partner_obj.sudo().browse(list_dict['partner_id']).street or '',cell_wrap_format)
            control_report_worksheet.write(row, 14, res_partner_obj.sudo().browse(list_dict['partner_id']).phone or '',cell_wrap_format)
            control_report_worksheet.write(row, 15, res_partner_obj.sudo().browse(list_dict['partner_id']).mobile or '', cell_wrap_format)
            control_report_worksheet.write(row, 16, res_partner_obj.sudo().browse(list_dict['partner_id']).email or '',cell_wrap_format)

            control_report_worksheet.write(row, 17, list_dict['prospect_name'], cell_wrap_format)
            control_report_worksheet.write(row, 18, list_dict['prospect_address'], cell_wrap_format)
            control_report_worksheet.write(row, 19, prospect_area_obj.sudo().browse(list_dict['prospect_area_id']).name or '', cell_wrap_format)
            control_report_worksheet.write(row, 20, list_dict['prospect_phone'], cell_wrap_format)
            control_report_worksheet.write(row, 21, list_dict['prospect_email'], cell_wrap_format)

            control_report_worksheet.write(row, 22, list_dict['root_cause'], cell_wrap_format)
            control_report_worksheet.write(row, 23, complaint_type_obj.sudo().browse(list_dict['complaint_type_support_id']).name or '', cell_wrap_format)
            control_report_worksheet.write(row, 24, list_dict['source_support'], cell_wrap_format)

            control_report_worksheet.write(row, 25, localize_tz(list_dict['last_log_datetime'], '%Y-%m-%d %H:%M:%S').astimezone(user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict['last_log_datetime'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 26, res_user_obj.browse(list_dict['last_log_user_id']).name or '',cell_wrap_format)
            control_report_worksheet.write(row, 27, list_dict['last_log_message'], cell_wrap_format)
            row += 1

