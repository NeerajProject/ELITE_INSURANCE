from odoo import fields, models, api , _
from odoo.exceptions import ValidationError

class  ProjectTask(models.Model):
    _inherit = 'project.task'

    branch_id = fields.Many2one('crm.team',related="project_id.team_id",store=True)
    insurance_company = fields.Many2one('res.partner',related='project_id.insurer_partner_id' ,store=True)
    producers_name = fields.Many2one('res.users',related='project_id.user_id' ,store=True)
    policy_type = fields.Many2one('insurance.type', string="Policy",related='project_id.insurance_type_id',store=True)
    policy_status = fields.Selection([
        ('draft', 'Draft'),
        ('approve_in_progress', 'Approval In Progress'),
        ('active', 'Active'),
        ('renewal_in_progress', 'Renewal InProgress'),
        ('renewed', 'Renewed'),
        ('expired', 'Expired')
    ], string='Policy Status' ,related="project_id.policy_status",store=True)


    premium_transaction_amt = fields.Float(string="Premium Transaction Amt",compute="_compute_premium_transaction_amt")
    premium_trasaction_ids = fields.One2many('premiums.payments.line','task_id',
                                             domain=[('status', '=', 'post'), ('is_selected', '!=', False)]
                                             )
    brokers_calculation_line_ids = fields.One2many('brokerage.calculation.line','task_id')
    commission_to_clamed = fields.Float(string="Commission Claimed" , compute="compute_commission_to_invoice")
    commission_received = fields.Float(string="Commission Received",compute="compute_commission_recieved")
    brokerage_collection_lines = fields.One2many('brokerage.collection.line','task_id')


    @api.depends('brokerage_collection_lines')
    def compute_commission_recieved(self):
        for rec in self:
            total = 0
            for record in rec.brokerage_collection_lines.filtered(lambda l: l.select and l.status == 'post'):
                total = total + record.commissions_allocation
            self.amount = total
            return total

    def get_invoice_brokers(self):
        return  self.env['account.move.line'].search([('task_brokerage_id','=',self.id)])


    @api.depends('brokers_calculation_line_ids')
    def compute_commission_to_invoice(self):
        for rec in self:
            total = 0
            for record in rec.brokers_calculation_line_ids.filtered(lambda l:l.select and l.status == 'post'):
                total=total + record.commissions_to_invoice
            self.amount = total
            return total




    @api.model
    def create(self, vals):
        res = super(ProjectTask, self).create(vals)
        res.compute_project_id_team_id()
        return res


    @api.depends('premium_trasaction_ids')
    def _compute_premium_transaction_amt(self):
        for rec in self:
            total = 0
            for lines in rec.premium_trasaction_ids:
               total = total + lines.payment_allocation
            rec.premium_transaction_amt = total
            rec.premium_paid_amount = total


    def action_premium_transaction(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'premiums.payments.line',
            'name': _("Premium Transaction"),
            'target': 'current',
            'views': [[False, 'list'], [False, 'form']],
            'domain':[('id','in',self.premium_trasaction_ids.ids)]
        }

    def compute_project_id_team_id(self):
        for rec in self:
            rec.branch_id = rec.project_id.team_id
            rec.insurance_company = rec.project_id.insurer_partner_id
            rec.producers_name = rec.project_id.user_id
            # rec.policy_type = rec.project_id.policy_type

    @api.model
    def create(self, vals):
        res = super(ProjectTask, self).create(vals)
        res.compute_project_id_team_id()
        return res
class PremiumsPaymentsLine(models.Model):
    _name = 'premiums.payments.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    # enter lines here
    task_id = fields.Many2one('project.task')
    project_id = fields.Many2one('project.project', compute="_compute_premium_payments_line")
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
    type_of_business = fields.Many2one('insurance.industry.type', string="Type of Business")
    producers_name = fields.Many2one('res.users', string="Producer Name")
    producers_commissions_rate = fields.Float(string="Producers Commissions Rate")
    due_date = fields.Date(string="Due date")
    rate_of_commissions = fields.Float(string="Rate of Commissions")
    total_premiums = fields.Float(string="Total Premiums")
    paid_amount = fields.Float(string="Paid Amount")
    outstanding_payment = fields.Float(string="Outstanding Payment")
    status = fields.Selection([
        ('not_invoiced', 'Not Invoiced'),
        ('draft', 'Draft'),
        ('invoiced', 'Invoiced'),
        ('partially_paid', 'Partially Paid'),
        ('fully_paid', 'Fully Paid')
    ], default='not_invoiced', string='Status')
    premium_transaction_amt = fields.Float(string="Transaction Amt")





    premiums_payments_id = fields.Many2one('premiums.payments',tracking=True)
    payment_allocation = fields.Float(string="Payments Allocation")
    brokerage_fee_status = fields.Selection([('not_invoiced', 'Not Invoiced'),
        ('draft', 'Draft'),
        ('invoiced', 'Invoiced'),
        ('partially_paid', 'Partially Paid'),
        ('fully_paid', 'Fully Paid')
    ], default='not_invoiced', string='Status')
    status = fields.Selection([('draft', 'Draft'), ('post', 'Post')], default="draft", string='Status')
    is_selected = fields.Boolean()



    def _compute_premium_payments_line(self):
        for rec in self:
            rec.name = rec.premiums_payments_id.name
            rec.project_id = rec.task_id.project_id
            rec.insurer_partner_id = rec.project_id.insurer_partner_id
            rec.odoo_policy = rec.project_id.policy_sequence
            rec.policy_no = rec.project_id.e_policy_no
            rec.schedule_no = rec.task_id.name
            rec.type_of_policy = rec.project_id.policy_type
            rec.customer_name_id = rec.project_id.partner_id
            rec.type_of_business = rec.project_id.industry_type_id
            rec.brokerage_fee_status = rec.task_id.brokerage_fee_status
            if rec.project_id.opportunity_id :
                rec.type_of_business = rec.project_id.opportunity_id.industry_type_id
            rec.producers_name = rec.project_id.user_id
            rec.producers_commissions_rate = rec.task_id.salesperson_commission_per
            rec.due_date = rec.task_id.date_deadline
            rec.rate_of_commissions=rec.project_id.brokerage_fee_per
            rec.total_premiums = rec.task_id.amount
            rec.paid_amount= rec.task_id.premium_paid_amount
            rec.outstanding_payment =  rec.total_premiums -  rec.paid_amount
            rec.premium_transaction_amt = rec.task_id.premium_transaction_amt
    @api.model
    def create(self, vals):
        res = super(PremiumsPaymentsLine, self).create(vals)
        res._compute_premium_payments_line()
        return res

class PremiumsPayments(models.Model):
    _name = 'premiums.payments'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(default=lambda self: _('New'),required=True,
                          readonly=True)


    branch_id = fields.Many2one('crm.team', string="Branch")
    premium_paid_amounts = fields.Float(string="Premium paid. Amounts" ,required=True,tracking=True)
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
    producers_name = fields.Many2one('res.users', string="Producers Name")
    policy_type = fields.Many2one('insurance.type', string="Policy")
    user_id = fields.Many2one('res.users',string="Producers Name")
    status = fields.Selection([('draft', 'Draft'), ('post', 'Post')], default="draft", string='Status',tracking=True)
    premiums_payments_line_ids = fields.One2many('premiums.payments.line','premiums_payments_id')

    total_amount = fields.Float(compute="_compute_total_line")

    def action_filters(self):
        # domain = [('task_type', '=', 'offerings')]
        domain = [('task_type', '=', 'premium_schedules'), ('parent_id', '!=', False)]

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
        if self.policy_status:
            domain.append(('policy_status','=',self.policy_status))
        if self.partner_id:
            domain.append(('partner_id','=',self.partner_id.id))
        if self.producers_name:
            domain.append(('salesperson_user_id','=',self.producers_name.id))

        print(domain)

        values = self.env['project.task'].search(domain)
        print(values)
        data=[]
        for rec in values:
            data.append((0, 0, {
                'task_id': rec.id
            }))
        for rec in self.premiums_payments_line_ids:
            rec.unlink()
        # self.premiums_payments_line_ids = [(5)]
        if values:
            self.premiums_payments_line_ids =data

    @api.depends('premiums_payments_line_ids')
    def _compute_total_line(self):
        for rec in self:
            print("rec -->",rec)
            print("premiums_payments_line_ids -->",rec.premiums_payments_line_ids)
            total = 0
            rec.total_amount =0
            for line in rec.premiums_payments_line_ids:
                print(line.read())
                total = total + line.payment_allocation
            rec.total_amount = total

    def action_post(self):

        if not(self.premium_paid_amounts - self.total_amount == 0):
            raise ValidationError(_('Premium Paid Amount is exceed the limit'))

        self.status = 'post'
        for line in self.premiums_payments_line_ids:
            if line.payment_allocation:
                line.is_selected=True
            line.status = "post"

    def action_cancel(self):
        self.status = 'draft'
        for line in self.premiums_payments_line_ids:
            if line.payment_allocation:
                line.is_selected=False
            line.status = "draft"

    def update_project_task(self):
        list = self.env['project.task'].search([])
        for rec in list:
            rec.compute_project_id_team_id()


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'res.premiums.payments') or _('New')
        res = super(PremiumsPayments, self).create(vals)
        return res