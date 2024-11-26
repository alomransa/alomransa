from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Probation(models.Model):
    _inherit = 'hr.contract'

    training_info = fields.Text(string='Probationary Info')
    waiting_for_approval = fields.Boolean()
    is_approve = fields.Boolean()
    state = fields.Selection(
        selection=[
            ('draft', 'New'),
            ('probation', 'Probation'),
            ('open', 'Running'),
            ('close', 'Expired'),
            ('cancel', 'Cancelled'),
        ],
    )
    probation_id = fields.Many2one('hr.training')
    half_leave_ids = fields.Many2many('hr.leave', string="Half Leave")
    training_amount = fields.Float(string='Training Amount', help="Amount for the employee during training")

    @api.onchange('trial_date_end')
    def state_probation(self):
        """
        Change state to 'probation' when 'trial_date_end' is set.
        """
        if self.trial_date_end:
            self.state = 'probation'

    @api.onchange('employee_id')
    def change_employee_id(self):
        """
        Update the employee_id in the related 'hr.training' record
        when employee_id changes in the contract.
        """
        if self.probation_id and self.employee_id:
            self.probation_id.employee_id = self.employee_id.id

    def action_approve(self):
        """
        Approve the contract and change the state from 'probation' to 'open'.
        """
        self.write({'is_approve': True})
        if self.state == 'probation':
            self.write({'state': 'open', 'is_approve': False})

    @api.model
    def create(self, vals_list):
        """
        Create a new probation record in 'hr.training' if the state is 'probation'.
        """
        if vals_list.get('trial_date_end') and vals_list.get('state') == 'probation':
            dtl = self.env['hr.training'].create({
                'employee_id': vals_list['employee_id'],
                'start_date': vals_list['date_start'],
                'end_date': vals_list['trial_date_end'],
            })
            vals_list['probation_id'] = dtl.id
        res = super(Probation, self).create(vals_list)
        return res

    def write(self, vals):
        """
        Handle state transitions and ensure proper validations for 'probation' contracts.
        """
        if self.state == 'probation':
            if vals.get('state') == 'open' and not self.is_approve:
                raise UserError(_("You cannot change the status of non-approved Contracts."))
            if vals.get('state') in ['cancel', 'close', 'draft']:
                raise UserError(_("You cannot change the status of non-approved Contracts."))
        training_dtl = self.env['hr.training'].search([('employee_id', '=', self.employee_id.id)])
        if training_dtl:
            return super(Probation, self).write(vals)
        if not training_dtl:
            if self.trial_date_end and self.state == 'probation':
                self.env['hr.training'].create({
                    'employee_id': self.employee_id.id,
                    'start_date': self.date_start,
                    'end_date': self.trial_date_end,
                })
        return super(Probation, self).write(vals)
