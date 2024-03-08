
class snippet():

    #pass values in a context variable
    ## ../ kin_sales / models / sale.py: 270
    def action_confirm(self):
        ctx = dict(self._context)
        ctx['atl_depot_id'] = self.location_id.id
        res = super(SaleOrder, self.with_context(ctx)).action_confirm()

    #ref ..odoo-custom-addons/kin_contract/models/contract.py:26
    def send_email_from_email_template(self):
        # send email to customer
        if is_send_recurring_email:
            template = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)
            if email_from:
                template.email_from = email_from
            if email_cc:
                template.email_cc = email_cc
            template.send_mail(res.id, force_send=False)

# ../odoo-custom-addons/kin_account/wizard/activity_statement_wizard_extend.py:13
    def send_mass_email_activity_statement(self, partners):
        company_email = self.env.user.company_id.email.strip()
        for partner in partners:
            partner_email = partner.email or False
            if company_email and partner_email:
                mail_template = partner.env.ref('kin_account.mail_template_partner_activity_statement_email')
                mail_template.send_mail(partner.id, force_send=False)
        return

    def action_statement_send(self):
        partner_id = self.env.context.get('active_ids', [])

        if len(partner_id) > 1:
            partners = self.env['res.partner'].browse(partner_id)
            self.send_mass_email_activity_statement(partners)

        else:
            template_id = self.env['ir.model.data'].xmlid_to_res_id(
                'kin_account.mail_template_partner_activity_statement_email', raise_if_not_found=False)

            ctx = {
                'default_model': 'res.partner',
                'default_res_id': partner_id[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                # 'mark_so_as_sent': True,
                # 'custom_layout': "mail.mail_notification_paynow",
                # 'proforma': self.env.context.get('proforma', False),
                'force_email': True
            }
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
            }

    #Access rights on fields with error notification
    allow_group_obj_users = self.env.ref('aminata_modifications.group_price_unit_allow').users
    if not self.env.user in allow_group_obj_users and self.type == 'product' and vals.get('list_price',False) or vals.get('sales_price_transport_charge', False):
        raise UserError(_('You are not allowed to edit the sales price or the sales price transport charge field for the stockable product'))

  #Some useful checks
    #../addons/aminata_modifications/aminata.py:1205
    def do_checks(self):
        # Finding duplicated in a list
        l = []
        for order_line in self.delivery_order_line_ids:
            l.append(order_line.partner_id.id)
        if set([x for x in l if l.count(x) > 1]):  # see https://stackoverflow.com/questions/9835762/find-and-list-duplicates-in-a-list
            raise UserError(( 'Duplicate Service Station detected. Only One Service Station is allowed at a time for each Station Delivery Order'))

        # Check total qty
        if self.total_product_qty != sum(self.delivery_order_line_ids.mapped('requested_qty')):
            raise UserError(_('Please The Total Product Qty to be Approved must be equal to the Sum of all Requested Qtys in the Lines below'))

    #ref: addons/kkon_modifications/report/ticket_report_xlsx.py:150
    # Timezone on excel report
    user_tz_obj = pytz.timezone(self.env.context.get('tz') or 'utc')
    localize_tz = pytz.utc.localize
    control_report_worksheet.write(row, 0, localize_tz(
        datetime.strptime(list_dict['assigned_date'], '%Y-%m-%d %H:%M:%S')).astimezone(user_tz_obj).strftime('%d/%m/%Y %H:%M:%S') if list_dict['assigned_date'] else '', cell_wrap_format)

    # Using any(  and any(not ...
    #source: ../addons/hr_expense/models/hr_expense.py:201
    if any(expense.state != 'approve' for expense in self):
        raise UserError(_("You can only generate accounting entry for approved expense(s)."))

    if any(not expense.journal_id for expense in self):
        raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

#../addons/aminata_modifications/aminata.py:1940
    #using all
    if all(rec.state == 'validate' for rec in self.station_distribution_id.station_product_dist_ids):
        total_lifted_qty = 0
    #reference: ../addons/kin_retail_station_general/retail_station.py:2316
    #Finding duplicated in a list
    if set([x for x in l if
            l.count(x) > 1]):  # see https://stackoverflow.com/questions/9835762/find-and-list-duplicates-in-a-list
        raise UserError(
            _('Duplicate Tank detected. Only One Tank is allowed at a time for each product received register'))


#Comapring two float numbers that should
precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
if float_compare(int_1, int2, precision_digits) != 0:
        raise UserError('No way')

#../addons/kin_loading/fibernet.py:2553
precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
if float_round(transfer_requested_qty, precision_digits) > float_round(qty_bal, precision_digits):
    raise UserError((_('Sorry, you cannot transfer product qty. that is more that the remaining balance qty.')))

# round a moneetary amount
lead.currency_id.round(amount_untaxed)

#Importing Files into Odoo
#../addons/account_bank_statement_import/account_bank_statement_import.py:29

        #changing the email_from and reply_to field in email
            partn_csc_ids = ''
            for user in csc_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_csc_ids += user.partner_id.email  + ", "
            if partn_csc_ids:
                mail_obj.email_from = partn_csc_ids
                mail_obj.reply_to = partn_csc_ids


        #sending carbon copy email
            csc_users = []
            user_t  False   False                                                                                                                                                    icket_groups = self.env.user.user_ticket_group_ids
            for user_ticket_group in user_ticket_groups :
                if user_ticket_group.is_csc_kkon_group or user_ticket_group.is_csc_fob_group:
                    csc_users = user_ticket_group.sudo().user_ids

            msg = 'The Ticket (%s) with description (%s), has been Opened by %s' % (
                self.ticket_id, self.name, self.env.user.name)
            partn_csc_ids = []
            for user in csc_users:
                if user.is_group_email:
                    user_names += user.name + ", "
                    partn_csc_ids.append(user.partner_id.id)
            if partn_csc_ids :
                mail_obj.email_partner_cc = partn_csc_ids

#sending email in odoo14
def send_email(self, grp_name, subject, msg):
    partn_ids = []
    user_names = ''
    group_obj = self.env.ref(grp_name)
    for user in group_obj.users:
        user_names += user.name + ", "
        partn_ids.append(user.partner_id.id)
    if partn_ids:
        # self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
        self.message_follower_ids.unlink()
        self.message_post(body=msg, subject=subject, partner_ids=partn_ids)
        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

#sending email
#../addons/kin_helpdesk/helpdesk.py:229
group_name = 'kin_helpdesk.group_helpdesk_receive_open_ticket_email'
msg = 'The Ticket (%s) with description (%s), has been Opened by %s' % (self.ticket_id, self.name, self.env.user.name)
self.send_email(group_name,msg)

def send_email(self, grp_name, msg):
    #..addons/kkon_modifications/ticket.py:88
    self.message_follower_ids.unlink() # This worked in the kkontech module for the cron job for checking for service relocation ticket
    # send email
    partn_ids = []
    group_obj = self.env.ref(grp_name)
    user_names = ''
    for user in group_obj.users:
        user_names += user.name + ", "
        partn_ids.append(user.partner_id.id)

    if partn_ids:
        # self.message_unsubscribe(partner_ids=[self.partner_id.id]) #this will not remove any other unwanted follower or group, there by sending to other groups/followers that we did not intend to send
        self.message_follower_ids.unlink()
        self.message_post(body=msg, subject=subject, partner_ids=partn_ids,subtype_xmlid='mail.mt_comment', force_send=False)
        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
    return

# Sending Email Notification
   # ../addons/kin_loading/fibernet.py:3943
    partn_ids = []
    user_names = ''
    group_obj = self.env.ref(
        'kin_loading.group_throughput_receipt_validate_notification')
    msg = 'The Throughput Receipt (%s) for (%s), has been validated by %s' % (
        self.name, self.customer_id.name, self.env.user.name)
    for user in group_obj.users:
        user_names += user.name + ", "
        partn_ids.append(user.partner_id.id)

    if partn_ids:
        self.message_post(
            _(msg),
            subject='%s' % msg, partner_ids=partn_ids)
    self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

#sending email that is raw without the bell and whistle
#see: odoo-custom-addons/fibernet/models/sale.py:526
    def action_receipt_plain_sent_no_logging_no_button_document(self):
        #this is just raw email without the default sent by footer, view button and there is no email log on the document

        partner_id = self.partner_id
        if not partner_id.email:
            raise UserError(
                'Kindly set the email for the %s with client id %s, in the customers database, before this ticket can be opened' % (
                    partner_id.name, partner_id.ref or ''))

        report = self.env.ref('kin_account.action_report_receipt')._render_qweb_pdf(self.id)
        name = '%s Payment Recieipt (%s)' % (self.env.company.name, self.name)
        filename = name + '.pdf'
        receipt = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(report[0]),
            'store_fname': filename,
            'res_model': 'account.payment',
            'res_id': self.id,
            # 'mimetype': 'application/x-pdf'
        })
        msg = "<p>Dear %s</p><p>Thank you for your payment. See attached document for your payment receipt %s amounting to %s from %s.</p><p>Do not hesitate to contact us if you have any questions.</p><p>Best regards,</p>" % (
        self.partner_id.name, (self.name or '').replace('/', '-'),
        format_amount(self.env, self.amount, self.currency_id), self.company_id.name)
        mail_values = {
            'subject': name,
            'body_html': msg,
            'author_id': self.env.user.partner_id.id,
            'email_from': 'csc@fibernet.ng',
            'email_to': self.partner_id.email,
            'attachment_ids': [(4, receipt.id)],
            'auto_delete': True
        }
        mail_values['attachment_ids'] += [(4, receipt.id)]
        mail = self.env['mail.mail'].sudo().create(mail_values)
        #mail.send()
        mail.mark_outgoing()



#Clear cache for Record Rules to take effect without restarting the server, for many2many fields. It does not apply to other type of fields
    @api.model
    def create(self, vals):
        self.clear_caches()
        return super(UserGroups,self).create(vals)

    # Clear cache for Record Rules to take effect without restarting the server, for many2many fields. It does not apply to other type of fields
    @api.multi
    def write(self, vals):
        # Record rules based on many2many relationship were not applied when many2many fields values were modified.
        #This not affect unlink/deletion or read() of records, so no need to clear cache for unlink() and read()
        self.clear_caches()  # ref: https://www.odoo.com/forum/help-1/question/force-odoo-to-delete-cache-81650
        return super(UserGroups,self).write(vals)
        # I have tested self.invalidate_cache(). It does not clear cache. so it should not be used



#How to use the read method
#../addons/kin_helpdesk/helpdesk.py:24
@api.multi
def read(self, fields=None, load='_classic_read'):
    res = super(UserGroups, self).read(fields=fields, load=load)
    return res


#overriding an excel report
#../addons/rog_modifications/wizard/pfa_report_wizard.py:9
class PFAReportWizard(models.TransientModel):
    _inherit = 'pfa.report.wizard'
#--/addons.rog_modifications.report.pfa_report_rog_xlsx.PFAReportWriter
PFAReportWriter('report.rog_modifications.report_pfa_excel_rog','pfa.report.wizard',parser=report_sxw.rml_parse)


#formatLang  uses
# ../addons/account/models/account_journal_dashboard.py:201
'account_balance': formatLang(self.env, account_sum, currency_obj=self.currency_id or self.company_id.currency_id),



#sh_message pop up code
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = "Task Created Successfully"
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }


#../addons/rog_modifications/hr.py:98
#writing into a computed field trick, by creating another field to save the value after the write operation
@api.depends('rule_type', 'no_of_days', 'gross_salary', 'month_wdays', 'month_days')
def compute_calculation(self):
    rule_type = self.rule_type
    month_wdays = self.month_wdays
    no_of_days = self.no_of_days
    month_days = self.month_days
    if rule_type in ['absent', 'absent_refund', 'lieo_refund', 'lwpr_refund'] and month_wdays and no_of_days:
        self.amount = (no_of_days * self.gross_salary) / self.month_wdays
    elif rule_type in ('lwpr_refund') and month_days and no_of_days:
        self.amount = (no_of_days * self.gross_salary) / month_days

@api.multi
def write(self, vals):
    other_amt = vals.get('other_amount', 0)
    res = super(RuleAdjustment, self).write(vals)
    if other_amt: # this is the trick to prevent it from overriding the previous value with the 0 value, and to prevent RuntimeError: maximum recursion depth exceeded
        self.amount = other_amt
    return res



    #open a create view from model
    @api.multi
    def create_bank_statement(self):
        """return action to create a bank statements. This button should be called only on journals with type =='bank'"""
        self.bank_statements_source = 'manual'
        action = self.env.ref('kin_bank_reconcile.action_bank_statement').read()[0]
        action.update({
            'views': [[False, 'form']],
            'context': "{'default_journal_id': " + str(self.id) + "}",
        })
        return action


#Sql Querying the Database
#../addons/account/models/account_journal_dashboard.py:162
    account_ids = tuple(filter(None, [self.default_debit_account_id.id, self.default_credit_account_id.id]))
    if account_ids:
        amount_field = 'balance' if not self.currency_id else 'amount_currency'
        query = """SELECT sum(%s) FROM account_move_line WHERE account_id in %%s;""" % (amount_field,)
        self.env.cr.execute(query, (account_ids,))
        query_results = self.env.cr.dictfetchall()
        if query_results and query_results[0].get('sum') != None:
            account_sum = query_results[0].get('sum')

#../addons.kin_bank_reconcile.bank_statement.BankStatement#get_gl_balance
    def get_gl_balance(self):
        journal_id = self.journal_id
        balance = 0
        if journal_id:
            account_ids = tuple(filter(None, [self.default_debit_account_id.id, self.default_credit_account_id.id]))
            if account_ids:
                amount_field = 'balance' if not self.currency_id else 'amount_currency'
                query = """SELECT sum(%s) FROM account_move_line WHERE account_id in %%s;""" % (amount_field,)
                self.env.cr.execute(query, (account_ids,))
                query_results = self.env.cr.dictfetchall()
                if query_results and query_results[0].get('sum') != None:
                    balance = query_results[0].get('sum')
        return balance

#search with order
last_bank_stmt = self.env['account.bank.statement'].search([('journal_id', 'in', self.ids)], order="date desc, id desc", limit=1)

#Using filtered
#../addons/kin_bank_reconcile/bank_statement.py:112
@api.multi
def unlink(self):
    for rec in self:
        is_true = rec.move_line_ids.filtered(lambda line: line.is_bank_reconciled == True)
        if is_true:
            raise UserError(_('Please unreconcile each line to delete the statement'))

    return super(BankStatement, self).unlink()

#ref: ../addons/kkon_modifications/crm.py:37
    crm_lead_obj = self.env['crm.lead'].search([('stage_id.probability', '=', '100'), ('date_won', '>=', start_date), ('date_won', '<=', end_date), ('user_id', '=', member.id)])
    for crm_lead in crm_lead_obj:
        #total_amount_taxed +=  crm_lead.product_line_ids.filtered(lambda line: line.product_id.is_mrc == True).mapped('price_total')[0] #raised error if the list is empty, so the safest option is to use the sum() function
        # OR
        total_amount_taxed +=  sum(crm_lead.product_line_ids.filtered(lambda line: line.product_id.is_mrc == True).mapped('price_total'))

    #ref: ../addons/purchase_request_to_rfq/models/purchase_request.py:25
    def filtered_mapped(self):
        self.purchased_qty = sum(self.purchase_lines.filtered(
                lambda x: x.state != 'cancel').mapped('product_qty'))

#ref: ../addons/purchase_request_to_rfq/models/purchase_request.py:63
    def selection_dynamics(self):
        purchase_state = fields.Selection(
            compute="_compute_purchase_state",
            string="Purchase Status",
            selection=lambda self:
            self.env['purchase.order']._columns['state'].selection,
            store=True,
        )


#../addons/hr_expense/models/hr_expense.py:120
    @api.multi
    def refuse_expenses(self, reason):
        self.write({'state': 'cancel'})
        if self.employee_id.user_id:
            body = (_("Your Expensssse %s has been refused.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (self.name, reason))
            self.message_post(body=body, partner_ids=[16], subtype_xmlid='mail.mt_comment', force_send=False)


    @api.multi
    def action_block_reason(self, msg):
        user_ids = []
        group_obj = self.env.ref('kin_loading.group_receive_block_ticket_notification')
        for user in group_obj.users:
            user_ids.append(user.partner_id.id)

            self.message_post(_(
                'The Loading Ticket (%s), belonging to %s, has been blocked by %s.') % (
                                  self.name, self.partner_id.name, self.env.user.name),
                              subject='A Loading Ticket has been blocked', partner_ids=[user_ids],
                              subtype_xmlid='mail.mt_comment', force_send=False)


#../odoo-rebranded-9.0/addons/kin_stock/stock.py:1124
    state = fields.Selection(selection_add=[('shipped', 'Shipped'),('delivered', 'Delivered'),('rejected', 'Rejected')])


    #simply means return the  products in the sales order lines.
    products = self.picking_id.sale_id.order_line.mapped('product_id')

    def snip_render_message(self):

# see ref ../odoo-9.0/addons/crm/crm_lead.py:399
        body_html = """<div><b>${object.next_activity_id.name}</b></div>
        %if object.title_action:
        <div>${object.title_action}</div>
        %endif"""
        text_msg = self.company_id.text_message
        body_html = self.env['mail.template'].render_template(text_msg, 'pos.order', self.id)

        self.message_post(body=body_html,
                          partner_ids=[(4, user.partner_id.id)],
                          subtype_xmlid='mail.mt_comment', force_send=False)


    #../odoo-9.0/addons/sale/sale.py:262
    @api.multi
    def action_view_invoice(self):
        invoice_ids = self.mapped('invoice_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(invoice_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % invoice_ids.ids
        elif len(invoice_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = invoice_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

  #  ../odoo - 9.0 / addons / custom / mine / kin_sms / kin_sms.py:33
    @api.multi
    def action_view_log(self):
        sms_log_ids = self.mapped('sms_log_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('kin_sms.sms_log_action')
        list_view_id = imd.xmlid_to_res_id('kin_sms.sms_log_tree')
        form_view_id = imd.xmlid_to_res_id('kin_sms.sms_log')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(sms_log_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % sms_log_ids.ids
        elif len(sms_log_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = sms_log_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


#../odoo-9.0/addons/sale/sale.py:829
class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    sale_line_ids = fields.Many2many('sale.order.line', 'sale_order_line_invoice_rel', 'invoice_line_id', 'order_line_id', string='Sale Order Lines', readonly=True, copy=False)




#.. /odoo-9.0/addons/stock_account/stock_account.py:34
def _get_price(self, cr, uid, inv, company_currency, i_line, price_unit):
    cur_obj = self.pool.get('res.currency')
    if inv.currency_id.id != company_currency:
        price = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, price_unit * i_line.quantity,
                                context={'date': inv.date_invoice})
    else:
        price = price_unit * i_line.quantity
    return round(price, inv.currency_id.decimal_places)




#PYTHON ENCRYPTION
#see reference: http://stackoverflow.com/questions/2490334/simple-way-to-encode-a-string-according-to-a-password
from Crypto.Cipher import AES

msg_text = 'kinco said'.rjust(32)
scrt_key = '141448459753079'.rjust(16)
cipher_obj = AES.new(scrt_key,AES.MODE_ECB)
encryted_text = cipher_obj.encrypt(msg_text).encode('hex')
decryted_text = cipher_obj.decrypt(encryted_text.decode('hex')).strip()

# filter a dictionary
list_dicts = filter(lambda line: line['hr_pfa_id'] == pfa.id, slist_dicts)  # reference: https://stackoverflow.com/a/25373204

#../odoo-rebranded-9.0/addons/kin_delivery/delivery_grid.py:422
sale_order_lines = self.sale_id.mapped('order_line') #Get the One2many records, then do the following line to search/filter by the parameters where  line.product_id.id == pack_operation_line.product_id
so_line = sale_order_lines.filtered(lambda line: line.product_id.id == pack_operation_line.product_id.id)


# ../odoo-9.0/addons/custom/mine/kin_pef/pef.py:188
# compute field helps recompute a field when the field is initialized/re-initialized for fields not represented as database table column. However, when store=True, it computes the field once at the point of initializing the field and stores it, without changing the stored value even after subsequent reads on the field. However, if you want the field to re-save new changing values, then the @depends() should be used to help recompute and store the new values for fields set as store=True
# Note that @api.depends does the work of @api.onchange. Also not @api.onchange does not persist  store=True fields
#see: odoo-9.0/addons/custom/mine/kin_retail_station/retail_station.py:471
total_pms_sales_qty = fields.Float('Total PMS Sales Qty.', compute='_amount_all', store=True)
#...odoo-9.0/addons/custom/mine/kin_retail_station/retail_station.py:490
@api.depends('retail_station_id')
def _compute_retail_station_manager(self):
    self.retail_station_manager_id = self.retail_station_id.retail_station_manager_id
retail_station_manager_id = fields.Many2one('res.users', compute='_compute_retail_station_manager',
                                                string='Retail Station Manager', store=True)


# ../addons/kin_account/res_partner.py:13
    @api.multi
    def name_get(self): # Works when you are reading the field name. e.g. when  tree view is loaded or form view is loaded
        result = []
        for partner in self:
            if partner.ref:
                strf = "%s - %s" % (partner.ref, partner.name)
                item = (partner.id, strf)
                result.append(item)
            else:
                result.append((partner.id, partner.name))
        return result

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100): # Works when you are searching for a field name on a many2one field or the search bar. it depicts how you you want to search
    #     args = args or []
    #     recs = self.browse()  # Initializes the variable, you can use recs = []
    #     if name:
    #         recs = self.search(['|', ('name', '=', name),('ref','=',name)] + args, limit=limit)
    #     if not recs:
    #         recs = self.search(['|', ('name', operator, name),('ref',operator,name)] + args, limit=limit)
    #     return recs.name_get()


#see ../odoo-11.0/addons/purchase/models/purchase.py:173
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('partner_ref', operator, name)]
        pos = self.search(domain + args, limit=limit)
        return pos.name_get()

    @api.multi
    @api.depends('name', 'partner_ref')
    def name_get(self):
        result = []
        for po in self:
            name = po.name
            if po.partner_ref:
                name += ' ('+po.partner_ref+')'
            if self.env.context.get('show_total_amount') and po.amount_total:
                name += ': ' + formatLang(self.env, po.amount_total, currency_obj=po.currency_id)
            result.append((po.id, name))
        return result

    #../odoo-rebranded-9.0/addons/kin_loading/fibernet.py:2246
    def sale_order():
        transfer_order_id = self.create({
            'partner_id': recipient_id.id,
            'partner_invoice_id': recipient_id.id,
            'partner_shipping_id': recipient_id.id,
            'pricelist_id': self.pricelist_id.id,
            'client_order_ref': self.name,
            'parent_sales_order_transfer_id': self.id,
            'order_line': [(0, 0, {
                'name': sale_order_line_id.product_id.name,
                'product_id': sale_order_line_id.product_id.id,
                'discount': sale_order_line_id.discount,
                'product_uom_qty': transfer_requested_qty,
                'product_uom': sale_order_line_id.product_uom.id,
                'price_unit': sale_order_line_id.price_unit,
            })],
        })

    # odoo - rebranded - 9.0 / addons / delivery / tests / test_delivery_stock_move.py:21
    def test_01_delivery_stock_move(self):
        # Test if the stored fields of stock moves are computed with invoice before delivery flow
        # Set a weight on ipod 16GB
        self.product_11.write({
            'weight': 0.25,
        })

        self.sale_prepaid = self.SaleOrder.create({
            'partner_id': self.partner_18.id,
            'partner_invoice_id': self.partner_18.id,
            'partner_shipping_id': self.partner_18.id,
            'pricelist_id': self.pricelist_id.id,
            'order_line': [(0, 0, {
                'name': 'Ice Cream',
                'product_id': self.product_icecream.id,
                'product_uom_qty': 2,
                'product_uom': self.product_uom_kgm.id,
                'price_unit': 750.00,
            })],
            'carrier_id': self.normal_delivery.id
        })

        # I add delivery cost in Sale order
        self.sale_prepaid.delivery_set()

        # I confirm the SO.
        self.sale_prepaid.action_confirm()
        self.sale_prepaid.action_invoice_create()

        # I check that the invoice was created
        self.assertEqual(len(self.sale_prepaid.invoice_ids), 1, "Invoice not created.")

        # I confirm the invoice

        self.invoice = self.sale_prepaid.invoice_ids
        self.invoice.signal_workflow('invoice_open')

        # I pay the invoice.
        self.invoice = self.sale_prepaid.invoice_ids
        self.invoice.signal_workflow('invoice_open')
        self.journal = self.AccountJournal.search([('type', '=', 'cash'), ('company_id', '=', self.sale_prepaid.company_id.id)], limit=1)
        self.invoice.pay_and_reconcile(self.journal, self.invoice.amount_total)

        # Check the SO after paying the invoice
        self.assertNotEqual(self.sale_prepaid.invoice_count, 0, 'order not invoiced')
        self.assertTrue(self.sale_prepaid.invoice_status == 'invoiced', 'order is not invoiced')
        self.assertEqual(len(self.sale_prepaid.picking_ids), 1, 'pickings not generated')

        # Check the stock moves
        moves = self.sale_prepaid.picking_ids.move_lines
        self.assertEqual(moves[0].product_qty, 2, 'wrong product_qty')
        self.assertEqual(moves[0].weight, 2.0, 'wrong move weight')

        # Ship
        self.picking = self.sale_prepaid.picking_ids.action_done()

#../addons.kkon_modifications.ticket.Ticket.create_customer_invoice
def create_customer_invoice(self, order):
    if not self.installation_date:
        raise UserError(_('Please Set the Installation Date'))

    if not self.config_status:
        raise UserError(_('Please Set the Configuration Status'))

    inv_obj = self.env['account.invoice']
    precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    invoices = {}

    journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
    if not journal_id:
        raise UserError(_('Please define an accounting sale journal for this company.'))

    sale_order = order
    invoice_vals = {
        'name': sale_order.name or '',
        'date_invoice': self.installation_date,
        'origin': sale_order.name,
        'type': 'out_invoice',
        'reference': sale_order.client_order_ref or self.name,
        'account_id': sale_order.partner_invoice_id.property_account_receivable_id.id,
        'partner_id': sale_order.partner_invoice_id.id,
        'journal_id': journal_id,
        'currency_id': sale_order.pricelist_id.currency_id.id,
        'comment': sale_order.note,
        'payment_term_id': sale_order.payment_term_id.id,
        # 'fiscal_position_id': sale_order.fiscal_position_id.id or sale_order.partner_invoice_id.property_account_position_id.id,  # this causes account not be found on the product category below. Please avoid it
        'company_id': sale_order.company_id.id,
        'user_id': sale_order.user_id and sale_order.user_id.id,
        'team_id': sale_order.team_id.id,
        'incoterms_id': sale_order.incoterm.id or False,
        'sale_id': sale_order.id,
        'is_installation_invoice': True,
        'installation_ticket_id': self.id,
    }
    invoice = inv_obj.create(invoice_vals)

    lines = []
    for sale_order_line_id in order.order_line:
        if not float_is_zero(sale_order_line_id.product_uom_qty, precision_digits=precision):
            account = sale_order_line_id.product_id.property_account_income_id or sale_order_line_id.product_id.categ_id.property_account_income_categ_id
            if not account:
                raise UserError(
                    _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % (
                        sale_order_line_id.product_id.name, sale_order_line_id.product_id.id,
                        sale_order_line_id.product_id.categ_id.name))

            default_analytic_account = self.env['account.analytic.default'].account_get(
                product_id=sale_order_line_id.product_id.id,
                partner_id=sale_order_line_id.order_id.partner_id.id,
                account_id=account.id,
                user_id=sale_order_line_id.order_id.user_id.id,
                date=date.today(),
                company_id=sale_order_line_id.company_id.id
            )

            inv_line = {
                'name': sale_order_line_id.name,
                'sequence': sale_order_line_id.sequence,
                'origin': sale_order_line_id.order_id.name,
                'account_id': account.id,
                'price_unit': sale_order_line_id.price_unit,
                'quantity': sale_order_line_id.product_uom_qty,
                'discount': sale_order_line_id.discount,
                'uom_id': sale_order_line_id.product_uom.id,
                'product_id': sale_order_line_id.product_id.id,
                # This will no longer causes the validated invoice to create COG entries from Goods Dispatched, because a service product is used instead of a stock product
                'invoice_line_tax_ids': [(6, 0, sale_order_line_id.tax_id.ids)],
                'account_analytic_id': sale_order_line_id.order_id.project_id.id or default_analytic_account and default_analytic_account.analytic_id.id,
                'invoice_id': invoice.id,
                'sale_line_ids': [(6, 0, [sale_order_line_id.id])]
                # Never remove this sale_line_ids. This determines the cost of goods sold using the FIFO and not from the product page
            }
            self.env['account.invoice.line'].create(inv_line)

    if not invoice.invoice_line_ids:
        raise UserError(_('There is no invoiceable line.'))
        # If invoice is negative, do a refund invoice instead
    if invoice.amount_untaxed < 0:
        invoice.type = 'out_refund'
        for line in invoice.invoice_line_ids:
            line.quantity = -line.quantity
    # Use additional field helper function (for account extensions)
    for line in invoice.invoice_line_ids:
        line._set_additional_fields(invoice)
        # Necessary to force computation of taxes. In account_invoice, they are triggered
        # by onchanges, which are not triggered when doing a create.
    invoice.compute_taxes()
    self.invoice_id = invoice

    # Send Email to accountants
    user_ids = []
    group_obj = self.env.ref('account.group_account_invoice')
    for user in group_obj.sudo().users:
        if user.is_group_email:
            user_ids.append(user.partner_id.id)

    if user_ids:
        invoice.message_post(_(
            'A New Installation Invoice has been created from  %s for the Ticket with ID %s.') % (
                                 self.env.user.name, self.name),
                             subject='A New Installation Invoice has been created ', partner_ids=[user_ids],
                             subtype_xmlid='mail.mt_comment', force_send=False)

    return invoice

#..addons/aminata_modifications/aminata.py:2213
        #Send email to initiator
        partn_ids = []
        user_name = self.user_id.name
        partn_ids.append(self.user_id.partner_id.id)

        if self.user_id.partner_id.email and partn_ids:
            msg = 'The Station to Station Transfer %s has been Reset by %s. Please edit and re-submit' % (
                self.name, self.env.user.name)
            self.message_post(_(msg),
                              subject='The Station to Station Transfer %s has been Reset by %s' % (self.name, self.env.user.name),
                              partner_ids=partn_ids)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_name))


#Send email with attachment
#..odoo-custom-addons/wifiber/models/sale.py:55
def send_sale_order_email(self):
    partner_id = self.partner_id
    if not partner_id.email:
        raise UserError(
            'Kindly set the email for the %s with client id %s, in the customers database, before this order can be sent' % (
                partner_id.name, partner_id.ref or ''))

    report = self.env.ref('sale.action_report_pro_forma_invoice')._render_qweb_pdf(self.id)
    name = '%s Proforma Invoice (%s)' % (self.env.company.name, self.name)
    filename = name + '.pdf'
    receipt = self.env['ir.attachment'].create({
        'name': filename,
        'type': 'binary',
        'datas': base64.b64encode(report[0]),
        'store_fname': filename,
        'res_model': 'sale.order',
        'res_id': self.id,
        # 'mimetype': 'application/x-pdf'
    })
    msg = "<p>Dear %s</p><p>Thank you for your order. See attached document for your proforma invoice %s amounting to %s from %s.</p><p>Do not hesitate to contact us if you have any questions.</p><p>Best regards,</p>" % (
        self.partner_id.name, (self.name or '').replace('/', '-'),
        format_amount(self.env, self.amount_total, self.currency_id), self.company_id.name)
    mail_values = {
        'subject': name,
        'body_html': msg,
        'author_id': self.env.user.partner_id.id,
        'email_from': 'sales@wifiber.ng',
        'email_to': self.partner_id.email,
        'attachment_ids': [(4, receipt.id)],
        'auto_delete': True
    }
    mail_values['attachment_ids'] += [(4, receipt.id)]
    mail = self.env['mail.mail'].create(mail_values)
    # mail.send()
    mail.mark_outgoing()



    # reference: https://stackoverflow.com/a/12691993
    # adds days except weekends
    def date_by_adding_business_days(self,from_date, add_days):
        business_days_to_add = add_days
        current_date = from_date
        while business_days_to_add > 0:
            current_date += timedelta(days=1)
            weekday = current_date.weekday()
            if weekday >= 5:  # saturday = 5 and sunday = 6
                continue
            business_days_to_add -= 1
        return current_date

    # odoo-custom-addons/fibernet/models/ticket.py:301
    # reference: https://stackoverflow.com/a/12691993
    # adds days except weekends
    def get_installation_date(self, from_date, add_days):
        business_days_to_add = add_days
        install_date = from_date
        while business_days_to_add > 0:
            install_date += timedelta(days=1)
            weekday = install_date.weekday()
            if weekday > 4:  # saturday = 5 and sunday = 6
                continue
            business_days_to_add -= 1
        return install_date