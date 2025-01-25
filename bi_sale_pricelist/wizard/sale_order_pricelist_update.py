# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from datetime import date


class SaleOrderPricelistWizard(models.Model):
    _name = 'sale.order.pricelist.wizard'
    _description = 'Pricelist Wizard'
    
    bi_wizard_pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")
    pricelist_line = fields.One2many('sale.order.pricelist.wizard.line', 'pricelist_id', string='Pricelist Line Id')

    @api.model
    def default_get(self, fields):
        res = super(SaleOrderPricelistWizard, self).default_get(fields)
        res_ids = self._context.get('active_ids')
        if res_ids and res_ids[0]:
            so_line = res_ids[0]
            so_line_obj = self.env['sale.order.line'].browse(so_line)
            pricelist_list = []
            # pricelists = self.env['product.pricelist'].sudo().search([])
            pricelists = self.env['product.pricelist'].sudo().search([
                ('applied_on', '=', 'product'),
                ('product_tmpl_id', '=', so_line_obj.product_id.product_tmpl_id.id)
            ])
            pricelist_item_id = fields.Many2one(
                'product.pricelist.item',
                string="Pricelist Item",
                store=True,  # تمكين التخزين
                compute='_compute_pricelist_item',  # إذا كان الحقل محسوبًا
                readonly=False  # اختياري، حسب الحاجة
            )
            if pricelists:
                for pricelist in pricelists:
                    price_rule = pricelist._compute_price_rule(
                        so_line_obj.product_id,
                        so_line_obj.product_uom_qty,
                        date=date.today(),
                        uom_id=so_line_obj.product_uom.id
                    )
                    price_unit = price_rule.get(so_line_obj.product_id.id, [0])[0]
                    margin = price_unit - so_line_obj.product_id.standard_price
                    if price_unit != 0.0:
                        margin_per = (100 * margin) / price_unit

                        wz_line_id = self.env['sale.order.pricelist.wizard.line'].create({
                            'bi_pricelist_id': pricelist.id,
                            'bi_unit_price': price_unit,
                            'bi_unit_measure': so_line_obj.product_uom.id,
                            'bi_unit_cost': so_line_obj.product_id.standard_price,
                            'bi_margin': margin,
                            'bi_margin_per': margin_per,
                            'line_id': so_line,
                        })
                        pricelist_list.append(wz_line_id.id)

            res.update({
                'pricelist_line': [(6, 0, pricelist_list)],
            })
        return res


class SaleOrderPricelistWizardLine(models.Model):
    _name = 'sale.order.pricelist.wizard.line'
    _description = 'Pricelist Wizard Line'

    pricelist_id = fields.Many2one('sale.order.pricelist.wizard', "Pricelist Id")
    bi_pricelist_id = fields.Many2one('product.pricelist', "Pricelist", required=True)
    bi_unit_measure = fields.Many2one('uom.uom', 'Unit')
    bi_unit_price = fields.Float('Unit Price')
    bi_unit_cost = fields.Float('Unit Cost')
    bi_margin = fields.Float('Margin')
    bi_margin_per = fields.Float('Margin %')
    line_id = fields.Many2one('sale.order.line')

    # def update_sale_line_unit_price(self):
    #     if self.line_id:
    #         # استدعاء حساب الحد الأدنى للسعر وتحديث الحقل
    #         minimum_price = self.calculate_minimum_price()
    #         self.line_id.write({
    #             'price_unit': self.bi_unit_price,
    #             'sh_sale_minimum_price': minimum_price,
    #         })
    def update_sale_line_unit_price(self):
        if self.line_id:
            minimum_price = self.calculate_minimum_price()
            self.line_id.write({
                'price_unit': self.bi_unit_price,
                'sh_sale_minimum_price': minimum_price if minimum_price else 0.0,
            })
    @api.depends('line_id')
    def _compute_pricelist_item(self):
        for record in self:
            record.pricelist_item_stored = record.line_id.pricelist_item_id

    # def calculate_minimum_price(self):
    #     """
    #     حساب الحد الأدنى للسعر بناءً على المنتج، قائمة الأسعار، ووحدة القياس.
    #     """
    #     product = self.line_id.product_id
    #     pricelist = self.bi_pricelist_id
    #     uom = self.bi_unit_measure
    #     partner = self.line_id.order_id.partner_id

    #     # التحقق من وجود المنتج وقائمة الأسعار
    #     if not product or not pricelist:
    #         return 0.0

    #     # حساب الحد الأدنى للسعر باستخدام قائمة الأسعار
    #     price_rule = pricelist._compute_price_rule(
    #         products=product,
    #         qty=1,  # يمكن تغييرها للكمية المطلوبة
    #         partner=partner,
    #         date=False,  # يمكن تحديد تاريخ معين
    #         uom_id=uom.id if uom else product.uom_id.id
    #     )

    #     # الحصول على السعر الأول من النتيجة
    #     minimum_price = price_rule.get(product.id, [0])[0]  # تأكد من أن المفتاح موجود
    #     return minimum_price
    def calculate_minimum_price(self):
        product = self.line_id.product_id
        pricelist = self.bi_pricelist_id
        uom = self.bi_unit_measure
        partner = self.line_id.order_id.partner_id
    
        if not product or not pricelist:
            return 0.0
    
        price_rule = pricelist._compute_price_rule(
            products=product,
            qty=1,
            partner=partner,
            date=False,
            uom_id=uom.id if uom else product.uom_id.id,
        )
    
        return price_rule.get(product.id, [0])[0] if product.id in price_rule else 0.0

    # @api.model
    # def filter_lines_by_pricelist_item(self, some_value):
    #     """
    #     فلترة الخطوط بناءً على قيمة `pricelist_item_id`.
    #     """
    #     lines = self.env['sale.order.line'].search([])
    #     filtered_lines = lines.filtered(lambda line: line.pricelist_item_id == some_value)
    #     return filtered_lines

# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'

#     pricelist_item_id = fields.Many2one('product.pricelist.item', store=True)

# # -*- coding: utf-8 -*-
# # Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

# from odoo import fields,models,api
# from datetime import date


# class SaleOrderPricelistWizard(models.Model):
#     _name = 'sale.order.pricelist.wizard'
#     _description = 'Pricelist Wizard'
    
#     bi_wizard_pricelist_id = fields.Many2one('product.pricelist',string="Pricelist")
#     pricelist_line = fields.One2many('sale.order.pricelist.wizard.line','pricelist_id',string='PricelistLine Id')
    
#     @api.model
#     def default_get(self, fields):
#         res = super(SaleOrderPricelistWizard, self).default_get(fields)
#         res_ids = self._context.get('active_ids')
#         if res_ids[0]:
#             so_line = res_ids[0]
#             so_line_obj = self.env['sale.order.line'].browse(so_line)
#             pricelist_list = []
#             pricelists = self.env['product.pricelist'].sudo().search([])
#             if pricelists:
#                 for pricelist in pricelists:
#                     price_unit =pricelist._compute_price_rule(so_line_obj.product_id, so_line_obj.product_uom_qty, date=date.today(), uom_id=so_line_obj.product_uom.id)[so_line_obj.product_id.id][0]
#                     margin = price_unit - so_line_obj.product_id.standard_price
#                     if price_unit != 0.0:
#                         margin_per = (100 * (price_unit - so_line_obj.product_id.standard_price))/price_unit
                             
#                         wz_line_id = self.env['sale.order.pricelist.wizard.line'].create({'bi_pricelist_id' :pricelist.id,
#                                                                                        'bi_unit_price':price_unit,
#                                                                                        'bi_unit_measure':so_line_obj.product_uom.id,
#                                                                                        'bi_unit_cost':so_line_obj.product_id.standard_price,
#                                                                                        'bi_margin':margin,
#                                                                                        'bi_margin_per':margin_per,
#                                                                                        'line_id': so_line,})
                         
#                         pricelist_list.append(wz_line_id.id)
#             res.update({
                
#                 'pricelist_line':[(6,0,pricelist_list)],
#             })
#         return res
        
        
        
# class SaleOrderPricelistWizardLine(models.Model):
#     _name = 'sale.order.pricelist.wizard.line'
#     _description = 'Pricelist Wizard'
    
#     pricelist_id = fields.Many2one('sale.order.pricelist.wizard',"Pricelist Id")
#     bi_pricelist_id = fields.Many2one('product.pricelist',"Pricelist",required=True)
#     bi_unit_measure = fields.Many2one('uom.uom','Unit')
#     bi_unit_price = fields.Float('Unit Price')
#     bi_unit_cost = fields.Float('Unit Cost')
#     bi_margin = fields.Float('Margin')
#     bi_margin_per = fields.Float('Margin %')
#     line_id =fields.Many2one('sale.order.line')
      
#     def update_sale_line_unit_price(self):
#         if self.line_id:
#             self.line_id.write({'price_unit':self.bi_unit_price})
        
              
