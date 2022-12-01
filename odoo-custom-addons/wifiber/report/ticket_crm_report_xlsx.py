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


class TicketReport(models.AbstractModel):
    _name = 'report.wifiber.ticket_crm_report'
    _inherit = 'report.report_xlsx.abstract'

    def _get_data(self, form):
        start_date = form['start_date']
        end_date = form['end_date']
        category_id = form['category_id'][0]
        company_id = form['company_id'][0]
        ticket_creator_id = form['ticket_creator_id']

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

        if ticket_creator_id :
            where_ticket_creator = "kin_ticket.create_uid = %s AND" % (ticket_creator_id)

        if category_id:
            where_category = "category_id = %s AND" % (category_id)

        if company_id:
            where_company = "ticket_company_id = %s AND" % (company_id)

        sql_statement = """

        ( SELECT
                  assigned_date,
                  ticket_id,
                  kin_ticket.name as name,
                  U1.id as user_name_id,
                  user_ticket_group_id,
                  open_date,
                  done_ticket_date,
                  closed_date,
                  time_spent,
                  state,
                  description,                  
                  U2.id as ticket_creator        
                FROM
                  kin_ticket
                  left JOIN res_users as U1 ON user_id = U1.id 
                  left JOIN res_users as U2 ON kin_ticket.create_uid = U2.id 
                WHERE
                    state != 'cancel' AND                   
                    """ + where_category + """ 
                     """ + where_company + """
                      """ + where_ticket_creator + """ 
                      """ + where_start_date + """
                       """ + where_end_date + """                       
                ORDER BY
                    assigned_date desc

                    ) 

                UNION

                (               
                SELECT
                  assigned_date,
                  ticket_id,
                  kin_ticket.name as name,
                  U1.id as user_name_id,
                  user_ticket_group_id,
                  open_date,
                  done_ticket_date,
                  closed_date,
                  time_spent,
                  state,
                  description,
                  U2.id as ticket_creator    
                FROM
                  kin_ticket
                  left JOIN res_users as U1 ON user_id = U1.id 
                  left JOIN res_users as U2 ON kin_ticket.create_uid = U2.id 
                WHERE
                    state != 'cancel' AND                   
                    """ + where_category + """ 
                     """ + where_company + """
                      """ + where_ticket_creator + """ 
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
        control_report_worksheet.set_column(1, 1, 15)
        control_report_worksheet.set_column(2, 2, 30)
        control_report_worksheet.set_column(3, 3, 15)
        control_report_worksheet.set_column(4, 4, 15)
        control_report_worksheet.set_column(5, 5, 15)
        control_report_worksheet.set_column(6, 6, 15)
        control_report_worksheet.set_column(7, 7, 15)
        control_report_worksheet.set_column(8, 8, 15)
        control_report_worksheet.set_column(9, 9, 15)
        control_report_worksheet.set_column(10, 10, 15)



        control_report_worksheet.write_row(row, col, (
            'DateTime', 'Ticket ID' ,'Title', 'Ticket Creator', 'Details' ,'Assigned Ticket Group',
            'Opened DateTime', 'Done DateTime', 'Closed DateTime', 'Time Spent', 'Stage',
            ), head_format)

        res_user_obj = self.env['res.users']
        user_ticket_group_obj = self.env['user.ticket.group']

        row += 1
        first_row = row
        for list_dict in list_dicts:
            control_report_worksheet.write(row, 0,
                                           localize_tz(list_dict['assigned_date'], '%Y-%m-%d %H:%M:%S').astimezone(
                                               user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict[
                                               'assigned_date'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 1, list_dict['ticket_id'], cell_wrap_format)
            control_report_worksheet.write(row, 2, list_dict['name'], cell_wrap_format)
            control_report_worksheet.write(row, 3, res_user_obj.browse(list_dict['ticket_creator']).name,
                                           cell_wrap_format)
            control_report_worksheet.write(row, 4, list_dict['description'], cell_wrap_format)

            control_report_worksheet.write(row, 5, user_ticket_group_obj.sudo().browse(
                list_dict['user_ticket_group_id']).name or '', cell_wrap_format)
            control_report_worksheet.write(row, 6, localize_tz(
                datetime.strptime(str(list_dict['open_date']), '%Y-%m-%d %H:%M:%S')).astimezone(user_tz_obj).strftime(
                '%d/%m/%Y %I:%M:%S %p') if list_dict['open_date'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 7, localize_tz(
                datetime.strptime(str(list_dict['done_ticket_date']), '%Y-%m-%d %H:%M:%S')).astimezone(
                user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict['done_ticket_date'] else '',
                                           cell_wrap_format)
            control_report_worksheet.write(row, 8, (
                localize_tz(datetime.strptime(str(list_dict['closed_date']), '%Y-%m-%d %H:%M:%S')).astimezone(
                    user_tz_obj).strftime('%d/%m/%Y %H:%%I:%M:%S %p:%S') if list_dict['closed_date'] else ''),
                                           cell_wrap_format)
            control_report_worksheet.write(row, 9, list_dict['time_spent'], cell_wrap_format)
            control_report_worksheet.write(row, 10, list_dict['state'], cell_wrap_format)
            row += 1

