from odoo import fields, models, api , _

class CommissionPayablesLine(models.Model):
    _name = 'commission.payable.line'
    task_id = fields.Many2one('project.task')
    project_id = fields.Many2one('project.project')
    commission_payable_id = fields.Many2one('commission.payable')
    insurance_company_id = fields.Many2one('res.partner',string="Insurance Co.")
    policy_sequence = fields.Char(string="Policy")
    schedule_no = fields.Float(string="End")
    type_of_policy = fields.Selection([
        ('new_policy', 'New Policy'),
        ('policy_renewal', 'Policy Renewal')
    ], string='Policy Type')
    customer_name_id = fields.Many2one('res.partner',string="Customer")
    producer_name_id = fields.Many2one('res.users',string="Producer Name")
    total_premium = fields.Float(string="Total Premium")
    total_premium_paid = fields.Float(string="Paid")
    total_premium_outstanding = fields.Float(string="O/S")
    elite_commission = fields.Float(string="Elite Commissions Rate (%)")
    elite_commission_amount = fields.Float(string="Elite Commissions  (SAR)")
    elite_commission_received = fields.Float(string="Received Commissions")
    commission_outstanding = fields.Float(string="Commissions - O/S")
    producer_commission_rate = fields.Float(string="Producers Commissions Rate")
    producer_commission = fields.Float(string="Producer Commission")
    producer_commission_paid = fields.Float(string="Paid")
    outstanding_producer_commission = fields.Float(string="O/S")
    select = fields.Boolean(string="Select")
    status = fields.Selection([('draft','Draft'),('post','Post')],default="draft")

    def _compute_premium_payments_line(self):
        for rec in self:
            rec.project_id = rec.task_id.project_id
            rec.insurance_company_id = rec.project_id.insurer_partner_id
            rec.policy_sequence = rec.project_id.policy_sequence
            rec.schedule_no = rec.project_id.no_of_premium_schedule
            rec.type_of_policy = rec.project_id.policy_type
            rec.customer_name_id = rec.project_id.partner_id
            rec.producer_name_id = rec.project_id.user_id
            rec.total_premium = rec.task_id.amount
            rec.total_premium_paid= rec.task_id.premium_paid_amount
            rec.total_premium_outstanding = rec.total_premium - rec.total_premium_paid
            rec.elite_commission = rec.project_id.brokerage_fee_per
            rec.elite_commission_amount = (rec.project_id.brokerage_fee_per*rec.total_premium)/100
            rec.elite_commission_received = rec.elite_commission_amount #from brokerage collection
            rec.commission_outstanding = rec.elite_commission_amount - rec.elite_commission_received
            rec.producer_commission_rate = rec.project_id.salesperson_commission_per
            rec.producer_commission = (rec.producer_commission_rate*rec.elite_commission_amount)/100
            rec.outstanding_producer_commission = rec.producer_commission - rec.producer_commission_paid




    @api.model
    def create(self, vals):
        res = super(CommissionPayablesLine, self).create(vals)
        res._compute_premium_payments_line()
        return res


class CommisionPayables(models.Model):
    _name ='commission.payable'


    name = fields.Char(default=lambda self: _('New'),required=True,
                          readonly=True)

    branch_id = fields.Many2one('crm.team', string="Branch")
    # premium_paid_amounts = fields.Float(string="Premium paid. Amounts", required=True, tracking=True)
    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    insurance_company = fields.Many2one('res.partner', string="Insurance Co.:")
    partner_id = fields.Many2one('res.partner', string="Customer Name")
    producers_name = fields.Many2one('res.users', string="Producers Name")
    policy_type = fields.Many2one('insurance.type', string="Policy")
    user_id = fields.Many2one('res.users', string="Producers Name")
    status = fields.Selection([('draft', 'Draft'), ('post', 'Post')], default="draft", string='Status', tracking=True)
    commission_payable_line = fields.One2many('commission.payable.line','commission_payable_id')



    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'commission.payable') or _('New')
        res = super(CommisionPayables, self).create(vals)
        return res

    def action_filters(self):
        # domain = [('task_type', '=', 'offerings')]

        domain = [('task_type', '=', 'premium_schedules'), ('parent_id', '!=', False)]
        if self.branch_id:
            domain.append(('branch_id', '=', self.branch_id.id))
        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))
        if self.insurance_company:
            domain.append(('insurance_company', '=', self.insurance_company.id))
        if self.policy_type:
            domain.append(('policy_type', '=', self.policy_type.id))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.user_id:
            domain.append(('salesperson_user_id', '=', self.user_id.id))

        values = self.env['project.task'].search(domain)
        print(values)
        data = []
        for rec in values:
            data.append((0, 0, {
                'task_id': rec.id
            }))
        for rec in self.commission_payable_line:
            rec.sudo().unlink()
        if values:
            self.commission_payable_line = data
