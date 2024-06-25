from odoo import fields, models, api , _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move.line'
    brokerage_calculation_line_id = fields.Many2one('brokerage.calculation.line')
class AccountMove(models.Model):
    _inherit = 'account.move'
    brokerage_calculation_id = fields.Many2one('brokerage.calculation')

    def action_invoice_register_payment(self):
        Payment = self.env['account.payment'].with_context(default_invoice_ids=[(4, self.id, False)])
        payment = Payment.create({
            'ref':"123",
            'partner_type': 'customer',
            'amount': self.amount_total,
            'date': self.invoice_date,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id
        })

class BrokerageCalculationLine(models.Model):
    _name = 'brokerage.calculation.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    task_id = fields.Many2one('project.task')
    project_id = fields.Many2one('project.project')
    # take value from  project.project insurance insurer_partner_id
    insurer_partner_id = fields.Many2one('res.partner', string="Insurance Co.", )
    # taking value from project.project sequence
    odoo_policy = fields.Char()
    # taking value from project.project policy_sequence
    policy_no = fields.Char()
    # taking value from project.project no_of_premium_schedule
    schedule_no = fields.Char()
    type_of_policy = fields.Selection([
        ('new_policy', 'New Policy'),
        ('policy_renewal', 'Policy Renewal')
    ], string='Policy Type')
    customer_name_id = fields.Many2one('res.partner', string="Cutomer Name")
    # type_of_business Customer Type FROM LEAD
    rate_of_commissions = fields.Float(string="Rate of Commissions")
    outstanding_payment = fields.Float(string="Outstanding Payment")
    status_fee_status = fields.Selection([
        ('not_invoiced', 'Not Invoiced'),
        ('draft', 'Draft'),
        ('invoiced', 'Invoiced'),
        ('partially_paid', 'Partially Paid'),
        ('fully_paid', 'Fully Paid')
    ], default='not_invoiced', string='Status')
    commissions_to_invoice = fields.Float()
    select = fields.Boolean()
    commission_to_clamed = fields.Float()

    brokerage_calculation_id = fields.Many2one('brokerage.calculation')
    status = fields.Selection([('draft','Draft'),('post','Post')],string="Status")

    total_premium_including_vat = fields.Float(string="Total Premium Including Vat")
    paid_including_vat = fields.Float(string="Paid Including Vat")
    commissions_eligible_excluding_vat = fields.Float(string="Commissions Eligible Excluding VAT")
    commission_outstanding_for_invoice = fields.Float(string="Commissions O/s for Invoice")
    commissions_invoice_vat = fields.Float(string="Commissions Invoice VAT")
    commission_invoice_including_vat = fields.Float(string="Commissions Invoice Including Vat")


    @api.onchange('select')
    def onchange_comissions_to_invoice(self):
        if self.select:
            self.commissions_to_invoice = self.outstanding_payment
        else:
            self.commissions_to_invoice = 0
    def _compute_brokerage_calculation_line(self):
        for rec in self:
            rec.project_id = rec.task_id.project_id
            rec.insurer_partner_id = rec.project_id.insurer_partner_id
            rec.odoo_policy = rec.project_id.sequence
            rec.policy_no = rec.project_id.policy_sequence
            rec.schedule_no = rec.project_id.no_of_premium_schedule
            rec.type_of_policy = rec.project_id.policy_type
            rec.customer_name_id = rec.project_id.partner_id
            rec.status_fee_status = rec.task_id.brokerage_fee_status
            rec.rate_of_commissions = rec.project_id.brokerage_fee_per
            rec.commission_to_clamed = rec.task_id.compute_commission_to_invoice()

            rec.total_premium_including_vat = rec.task_id.premium_vat_amount
            rec.paid_including_vat = rec.task_id.premium_paid_amount
            rec.outstanding_payment =  rec.total_premium_including_vat -  rec.paid_including_vat
            rec.commissions_eligible_excluding_vat = (rec.paid_including_vat/1.15)*rec.rate_of_commissions
            rec.commission_outstanding_for_invoice = rec.commissions_eligible_excluding_vat - rec.commission_to_clamed


    @api.model
    def create(self, vals):
        res = super(BrokerageCalculationLine, self).create(vals)
        res._compute_brokerage_calculation_line()
        return res

class BrokerageCalculation(models.Model):
    _name = 'brokerage.calculation'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(default=lambda self: _('New'),required=True,
                          readonly=True)


    branch_id = fields.Many2one('crm.team', string="Branch")
    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    insurance_company = fields.Many2one('res.partner', string="Insurance Co.:")
    policy_status = fields.Selection([
        ('draft', 'Draft'),
        ('approve_in_progress', 'Approval In Progress'),
        ('active', 'Active'),
        ('renewal_in_progress', 'Renewal InProgress'),
        ('renewed', 'Renewed'),
        ('expired', 'Expired')
    ], default='draft', string='Policy Status')
    partner_id = fields.Many2one('res.partner', string="Customer Name")
    policy_type = fields.Many2one('insurance.type', string="Policy")
    user_id = fields.Many2one('res.users',string="Producers Name")
    status = fields.Selection([('draft', 'Draft'), ('post', 'Post')], default="draft", string='Status',tracking=True)
    premiums_payments_line_ids = fields.One2many('premiums.payments.line','premiums_payments_id')
    brokerage_calculation_line_ids = fields.One2many('brokerage.calculation.line','brokerage_calculation_id')

    total_amount = fields.Float(compute="_compute_total_line")


    def action_get_invoice(self):
        self.ensure_one()
        return {
            'name': _('Groups'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('brokerage_calculation_id','=', self.id)],
            'target': 'current',
        }
    def action_post(self):
        self.status = 'post'
        for rec in self.brokerage_calculation_line_ids:
            rec.status = 'post'
        invoices =[]
        project_id ={}
        partner_id = {}
        for rec in self.brokerage_calculation_line_ids.filtered(lambda p: p.select):
            project_id[rec.project_id.id] =[]
        for rec in self.brokerage_calculation_line_ids.filtered(lambda p: p.select):
            project_id[rec.project_id.id ].append((0, 0, {
                'name': f'{rec.insurer_partner_id.name}|{rec.policy_no}|{rec.schedule_no}',
                'quantity': 1,
                'price_unit': rec.commissions_to_invoice,
                'tax_ids': False,
                'brokerage_calculation_line_id':rec.id
            }))
            partner_id[rec.project_id.id] = rec.project_id.insurer_partner_id.id
        print('partner_id',partner_id)
        print('project_id',project_id)
        for rec in project_id.keys():
            account_move_id=self.env['account.move'].create({
                'move_type': 'out_invoice',
                'brokerage_calculation_id':self.id,
                'partner_id': partner_id[rec],
                'invoice_line_ids':project_id[rec]
                                                })
            account_move_id.action_post()
            account_move_id.action_invoice_register_payment()

            # return account_move_id.action_invoice_register_payment()


            # context = {
            #     'payment_type': 'inbound',
            #     'partner_type': 'customer',
            # }
            # self.env['account.payment'].with_context(context)

    @api.depends('brokerage_calculation_line_ids')
    def _compute_total_line(self):
        total = 0
        for rec in self.brokerage_calculation_line_ids:
            if rec.select:
                total = total+rec.commissions_to_invoice
        self.total_amount = total


    def action_filters(self):
        # domain = [('task_type', '=', 'offerings')]
        print(">>>>>>>> self.producers_name", self.user_id)

        domain = [('task_type', '=', 'premium_schedules'), ('parent_id', '!=', False)]
        print(domain)
        if self.branch_id:
            domain.append(('branch_id','=',self.branch_id.id))
        if self.date_from:
            domain.append(('date','>=', self.date_from ))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))
        if self.insurance_company:
            domain.append(('insurance_company','=',self.insurance_company.id))
        if self.policy_type:
            domain.append(('policy_type','=',self.policy_type.id))
        if self.partner_id:
            domain.append(('partner_id','=',self.partner_id.id))
        if self.user_id:
            domain.append(('salesperson_user_id','=',self.user_id.id))
        print(domain)

        values = self.env['project.task'].search(domain)
        print(values)
        data=[]
        for rec in values:
            data.append((0, 0, {
                'task_id': rec.id
            }))
        for rec in self.brokerage_calculation_line_ids:
            rec.sudo().unlink()
        # self.premiums_payments_line_ids = [(5)]
        if values:
            self.brokerage_calculation_line_ids =data


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'brokerage.calculation') or _('New')
        res = super(BrokerageCalculation, self).create(vals)
        return res