from odoo import fields, models


class ExpressShipForSales(models.Model):
    _inherit = 'sale.order.line'

    express_shipping = fields.Boolean(string='Exp')


class ExpressShippingOrder(models.Model):
     _inherit = "sale.order"

     def _action_confirm(self):
         res_super = super()._action_confirm()
         is_express_shipping = False
         print(self)
         for line in self.order_line:
             if line.express_shipping:
                is_express_shipping = True
                break
         if is_express_shipping and len(self.order_line)>1:
             new_val = {}
             new_val['origin'] = self.name
             new_val['sale_id'] = self.id
             new_val['user_id'] = False
             new_val['move_type'] = 'direct'
             new_val['company_id'] = self.company_id.id
             new_val['partner_id'] = self.partner_shipping_id.id
             new_val['picking_type_id'] = 2
             new_val['location_id'] = self.warehouse_id.lot_stock_id.id
             new_val['location_dest_id'] = self.partner_shipping_id.property_stock_customer.id
             if self.procurement_group_id:
                 new_val['group_id'] = self.procurement_group_id.id
             new_pick = self.env['stock.picking'].create(new_val)

         return res_super
