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

class SalesAtlReport(models.TransientModel):
    _name = 'report.heyden.sales_atl_excel'
    _inherit = 'report.report_xlsx.abstract'

    def _get_discharged_qty(self,form):
        product_ids = form['product_ids']
        lot_id = form['lot_id']
        sales_atl_location_ids = form['sales_atl_location_ids']

        where_prod = ''
        if product_ids:
            where_prod = "product_id in (%s) AND" % ','.join(str(pr_id) for pr_id in product_ids)

        where_lot = ''
        if lot_id:
            where_lot = "lot_id in (%s) AND" % (lot_id[0])

        where_loc = ''
        if sales_atl_location_ids:
            where_loc = "location_dest_id in (%s) AND" % ','.join(str(sl_id) for sl_id in sales_atl_location_ids)

        sql_statement = """SELECT sum(qty_done)
                                  FROM stock_move_line
                                  WHERE
                                 """ + where_lot + """
                                 """ + where_prod + """                        
                                 """ + where_loc + """
                                 state IN ('done')
                                """
        self.env.cr.execute(sql_statement)
        dictAll = self.env.cr.dictfetchall()
        return dictAll


    def _get_data(self,form):
        type = form['type']
        product_ids = form['product_ids']
        lot_id = form['lot_id']
        sales_atl_location_ids = form['sales_atl_location_ids']

        where_type = ''
        if type == 'is_throughput':
            where_type = "sp.is_throughput_ticket = True AND"
        elif type == 'is_internal_use':
            where_type = "sp.is_internal_use_ticket = True AND"
        elif type == 'is_indepot':
            where_type = "sp.is_indepot_ticket = True AND"
        elif type == 'all':
            where_type = ""

        where_prod = ''
        if product_ids :
            where_prod = "sm.product_id in (%s) AND" % ','.join(str(pr_id) for pr_id in product_ids)

        where_lot = ''
        if lot_id:
            where_lot = "sml.lot_id in (%s) AND" % (lot_id[0])

        where_loc = ''
        if sales_atl_location_ids:
            where_loc = "sm.location_id in (%s) AND" % ','.join(str(sl_id) for sl_id in sales_atl_location_ids)

        # LEFT JOIN works similar to INNER JOIN but with the extra advantage of showing empty join parameter fields (uncompulsory join fields). It is good for join fields that don't have value. It will still show the records. Unlike INNER JOIN (for compulsory join fields) which will omit those records
        sql_statement = """SELECT row_number() over(order by sm.date) as sn, sm.id, sm.origin, sm.product_uom, sm.price_unit,
                                sm.product_uom_qty, sm.company_id, sm.date,   sm.location_id,
                                sm.picking_type_id, sm.state, sm.partner_id, sm.product_id,  sm.picking_id, sm.location_dest_id,
                                sm.purchase_line_id, sm.sale_line_id, sml.qty_done, spl.name as vessel ,atl_id, atl_date,
                                sm.name as product_name, sl.name as stock_location_name, pn.name as partner_name,
                                sp.waybill_no,  sp.truck_no, loaded_date,
                                address, receiving_station_management, receiving_manager_phone, truck_driver_phone,
                                is_block_ticket, is_loading_ticket, is_exdepot_ticket, loader_partner.name as loader_name, dispatch_date, sp.dpr_no, location_addr_id as location , sp.name as ticket_name,  sp.picking_type_code
                          FROM stock_move_line as sml
                          LEFT JOIN stock_production_lot as spl
                          ON sml.lot_id = spl.id 
                          LEFT JOIN stock_move as sm 
                          ON sml.move_id = sm.id
                          LEFT JOIN stock_location as sl
                          ON sm.location_id = sl.id
                          LEFT JOIN stock_picking as sp
                          ON sm.picking_id = sp.id
                          LEFT JOIN res_partner as pn
                          ON sm.partner_id = pn.id
                          LEFT JOIN res_users as loader
                          ON sp.loader_id = loader.id
                          LEFT JOIN res_partner as loader_partner
                          ON loader.id = loader_partner.id    
                          LEFT JOIN sale_order_line 
                          ON sm.sale_line_id = sale_order_line.id 
                          LEFT JOIN sale_order
                          ON sale_order_line.id = sale_order.id 
                          LEFT JOIN stock_move_line
                          ON sale_order_line.id = stock_move_line.id 
                          LEFT JOIN dpr_info 
                          ON sp.dpr_info_id = dpr_info.id
                          WHERE
                           """ + where_type +"""
                         """ + where_lot + """
                         """ + where_prod + """      
                         """ + where_loc + """
                         sm.state IN ('done')
                        """
        self.env.cr.execute(sql_statement)
        dictAll = self.env.cr.dictfetchall()

        return dictAll


    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        list_dicts = self._get_data(data['form'])
        discharged_qty = self._get_discharged_qty(data['form'])[0]['sum']

        product_ids = data['form']['product_ids']
        if not product_ids:
            pro_ids = self.env['product.product'].search([('type', '=', 'product')])
            for pr_id in pro_ids:
                product_ids.append(pr_id.id)

        stock_dispatch_location_ids = data['form']['sales_atl_location_ids']
        stklocs = ''
        if stock_dispatch_location_ids:
            for sdl_id in stock_dispatch_location_ids:
                sl_name = self.env['stock.location'].browse(sdl_id).name
                stklocs += ',' + sl_name
        else:
            stklocs = 'All Depots'

        report_worksheet = workbook.add_worksheet('SALES/ATL Report')
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

        # Vessel
        lot_obj = self.env['stock.production.lot']
        lot_id = data['form']['lot_id']

        type = data['form']['type']
        if type == 'is_throughput':
            report_worksheet.merge_range(2, 0, 2, 10, 'SALES/ATL Throughput Report for %s ' % stklocs.strip(','), title_format)
        elif type == 'is_internal_use':
            report_worksheet.merge_range(2, 0, 2, 10, 'SALES/ATL Internal Use Report for %s ' % stklocs.strip(','), title_format)
        elif type == 'is_indepot':
            report_worksheet.merge_range(2, 0, 2, 10, 'SALES/ATL In Depot Stock Report for %s ' % stklocs.strip(','), title_format)
        elif type == 'all':
            report_worksheet.merge_range(2, 0, 2, 10, 'All SALES/ATL Report for %s ' % stklocs.strip(','), title_format)

        report_worksheet.set_row(3, 20)
        report_worksheet.merge_range(3, 0, 3, 10, 'DISCHARGED QTY: %s    VESSEL: %s' % ('{:,.2f}'.format(discharged_qty) ,lot_obj.browse(lot_id[0]).name)  , title_format)

        col = 0
        row = 3
        report_worksheet.set_column(0, 0, 3)
        report_worksheet.set_column(1, 1, 15)
        report_worksheet.set_column(2, 2, 10)
        report_worksheet.set_column(3, 3, 20)
        report_worksheet.set_column(4, 20, 10)

        product_obj = self.env['product.product']
        for product_id in product_ids:
            report_worksheet.set_row(row, 20)
            row += 2
            product_name = product_obj.browse(product_id).name
            report_worksheet.merge_range(row, col, row, 9, product_name, title_format)
            row += 2

            report_worksheet.write_row(row, col, ('S/N', 'ATL NO.', 'ATL DATE','ATL NAME' , 'ATL QTY', 'CUM. ATL QTY' , 'BAL. QTY'  , 'TRUCK NO.' ,'LOADED DATE','DISPATCHED DATE','LOCATION' , 'SOURCE REF', 'TICKET ID' ,'WAYBILL NO.', 'DEPOT','DESTINATION') , head_format)
            row += 1
            total_qty = 0
            first_row = row
            a1_notation_total_qty_start = xl_rowcol_to_cell(row, 1)
            cum_qty = 0
            cum_bal = discharged_qty
            for list_dict in list_dicts:
                if list_dict['product_id'] == product_id:
                    if list_dict['picking_type_code'] == 'incoming':
                        product_uom_qty = -list_dict['qty_done']
                    else:
                        product_uom_qty = list_dict['qty_done']
                    cum_qty += product_uom_qty
                    cum_bal -= product_uom_qty
                    report_worksheet.write(row, 0, list_dict['sn'],cell_wrap_format)
                    report_worksheet.write(row, 1, list_dict['atl_id'], cell_wrap_format)
                    report_worksheet.write(row, 2, list_dict['atl_date'] and list_dict['date'].strftime('%d/%m/%Y %H:%M:%S'), cell_wrap_format) or False
                    report_worksheet.write(row, 3, list_dict['partner_name'], cell_wrap_format)
                    report_worksheet.write(row, 4, product_uom_qty, cell_number)
                    report_worksheet.write(row, 5, cum_qty, cell_number)
                    report_worksheet.write(row, 6, cum_bal, cell_number)
                    report_worksheet.write(row, 7, list_dict['truck_no'], cell_wrap_format)
                    report_worksheet.write(row, 8, list_dict['loaded_date'] and list_dict['loaded_date'].strftime('%d/%m/%Y'), cell_wrap_format) or False
                    report_worksheet.write(row, 9, list_dict['dispatch_date'] and list_dict['dispatch_date'].strftime('%d/%m/%Y'), cell_wrap_format) or False
                    report_worksheet.write(row, 10, list_dict['location'], cell_wrap_format)
                    report_worksheet.write(row, 11, list_dict['origin'], cell_wrap_format)
                    report_worksheet.write(row, 12, list_dict['ticket_name'], cell_wrap_format)
                    report_worksheet.write(row, 13, list_dict['waybill_no'], cell_wrap_format)
                    report_worksheet.write(row, 14, list_dict['stock_location_name'], cell_wrap_format)
                    report_worksheet.write(row, 15, list_dict['address'], cell_wrap_format)

                    row += 1
                    total_qty += product_uom_qty
                last_row  = row
                a1_notation_ref = xl_range(first_row, 4, last_row, 4)
                report_worksheet.write(row, 4, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_qty)
            row += 1
        return

