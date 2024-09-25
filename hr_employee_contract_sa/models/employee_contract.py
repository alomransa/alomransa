from odoo import models, fields

class EmployeeContract(models.Model):
    _name = 'hr.employee.contract'
    _description = 'Employee Contract'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    contract_date = fields.Date(string='Contract Date', required=True)
    contract_type = fields.Selection([
        ('fixed', 'Fixed Term'),
        ('permanent', 'Permanent'),
    ], string='Contract Type', required=True)
    salary = fields.Float(string='Salary', required=True)
    duration = fields.Integer(string='Contract Duration (Months)')
    job_title = fields.Char(string='Job Title', required=True)
    terms = fields.Text(string='Terms and Conditions')
