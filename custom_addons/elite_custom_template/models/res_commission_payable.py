from odoo import fields, models, api


class ResCommissionPayableLine(models.Model):
    _name = "res.commission.payable.line"
    task_id = fields.Many2one('project.task')
    project_id = fields.Many2one('project.project', related="task_id.project_id")
    commission_payable_id = fields.Many2one('res.commission.payable')
    # take value from  project.project insurance insurer_partner_id
    insurer_partner_id = fields.Many2one('res.partner', string="Insurance Co.")
    # taking value from project.project sequence
    odoo_policy = fields.Char()
    #taking value from project.project policy_sequence
    policy_no= fields.Char()
    #taking value from project.project no_of_premium_schedule
    schedule_no = fields.Integer()
    type_of_policy =fields.Selection([
        ('new_policy', 'New Policy'),
        ('policy_renewal', 'Policy Renewal')
    ], string='Policy Type')
    customer_name_id = fields.Many2one('res.partner', string="Cutomer Name")
    # type_of_business Customer Type FROM LEAD
    type_of_business = fields.Many2one('insurance.customer.type')
    producers_name = fields.Char()
    producers_commissions_rate = fields.Float(string="Producers Commissions Rate")
    due_date = fields.Date(string="Due date")
    rate_of_commissions = fields.Float(string="Rate of Commissions")
    total_premiums = fields.Float(string="Total Premiums")
    paid_amount = fields.Float(string="Paid Amount")
    outstanding_payment = fields.Float(string="Outstanding Payment")
    status = fields.Char(string="Status")
    premium_paid_before = fields.Float(string="Payments Allocation")



class ResCommissionPayable(models.Model):
    _name = 'res.commission.payable'

    # Filter widget of commission payable screen
    name = fields.Char()
    branch_id = fields.Many2one('crm.team', string="Branch")
    premium_paid_amounts = fields.Float(string="Premium paid. Amounts")
    date_from_date = fields.Date(string="From")
    date_to_date = fields.Date(string="To")
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
    commission_payable_line_ids = fields.One2many('res.commission.payable.line', 'commission_payable_id')
