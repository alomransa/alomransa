from odoo import models, _,fields,api
from odoo.exceptions import UserError


class SaleAccessButtons(models.Model):
    _inherit = 'sale.order'

    readonly_price = fields.Boolean(string="Belongs to Group", compute='_compute_belongs_to_group')

     def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        # إضافة أو تعديل الحقول المطلوبة هنا
        return invoice_vals
    def action_confirm(self):
        res = super(SaleAccessButtons, self).action_confirm()
        if self.env.user.has_group('sb_group_access.cannot_confirm_sale_orders'):
            raise UserError(_("You are not authorized to confirm sales orders."))
        return res

    def action_cancel(self):
        res = super(SaleAccessButtons, self).action_cancel()
        if self.env.user.has_group("sb_group_access.cannot_cancel_sale_orders"):
            raise UserError(_("You are not authorized to cancel sales orders."))
        return res

    def _create_invoices(self, grouped=False, final=False, date=None):
        res = super(SaleAccessButtons, self)._create_invoices()
        if self.env.user.has_group("sb_group_access.cannot_creat_invoice"):
            raise UserError(_("You are not authorized to creat invoices."))
        return res

    @api.depends('order_line')
    def _compute_belongs_to_group(self):
        for rec in self:
            rec.readonly_price = self.env.user.has_group('sb_group_access.cannot_edit_unit_price')
