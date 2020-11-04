from odoo import fields, models
from odoo.tools import float_compare

class ExpressShipForSales(models.Model):
    _inherit = 'sale.order.line'

    express_shipping = fields.Boolean(string='Exp')

    def _get_procurement_group_is_express(self):
        if self.express_shipping:
            return self.order_id.procurement_group_id_express
        else:
            return self.order_id.procurement_group_id


class SaleOrder(models.Model):
     _inherit = "sale.order"
     procurement_group_id_express = fields.Many2one('procurement.group', 'Procurement Group For express Shipping', copy=False)

     def _run_procurement_for_lines(self, lines, previous_product_uom_qty=False):

         precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
         procurements = []
         for line in lines:
             if line.state != 'sale' or not line.product_id.type in ('consu','product'):
                 continue
             qty = line._get_qty_procurement(previous_product_uom_qty)
             if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                 continue

             group_id = line._get_procurement_group_is_express()
             if not group_id:
                 group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                 if line.express_shipping:
                     line.order_id.procurement_group_id_express = group_id
                 else:
                     line.order_id.procurement_group_id = group_id
             else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                 updated_vals = {}
                 if group_id.partner_id != line.order_id.partner_shipping_id:
                     updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                 if group_id.move_type != line.order_id.picking_policy:
                     updated_vals.update({'move_type': line.order_id.picking_policy})
                 if updated_vals:
                     group_id.write(updated_vals)

             values = line._prepare_procurement_values(group_id=group_id)
             product_qty = line.product_uom_qty - qty

             line_uom = line.product_uom
             quant_uom = line.product_id.uom_id
             product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
             procurements.append(self.env['procurement.group'].Procurement(
                 line.product_id, product_qty, procurement_uom,
                 line.order_id.partner_shipping_id.property_stock_customer,
                 line.name, line.order_id.name, line.order_id.company_id, values))
             if procurements:
                 self.env['procurement.group'].run(procurements)
         return True

     def _action_confirm_with_express(self):

         exp_lines = self.order_line.filtered(lambda line: line.express_shipping)

         if len(exp_lines)>0 and len(self.order_line)>1:
             self._run_procurement_for_lines(exp_lines)
             not_exp = self.order_line.filtered(lambda line: not line.express_shipping)
             self._run_procurement_for_lines(not_exp) 
         else:
             self._action_confirm()

         return True

     def action_confirm(self):
         if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

         for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
             order.message_subscribe([order.partner_id.id])
         self.write({
             'state': 'sale',
             'date_order': fields.Datetime.now()
         })
         self._action_confirm_with_express()
         if self.env.user.has_group('sale.group_auto_done_setting'):
             self.action_done()
         return True


