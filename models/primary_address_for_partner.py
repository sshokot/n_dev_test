from odoo import fields, models
from odoo.exceptions import UserError


class PrimaryAddressForPartner(models.Model):
    _inherit = 'res.partner'

    primary_address = fields.Boolean()

    def write(self, values):
        not_allowed = False

        partners = self.env['res.partner']
        address_ids = self.mapped('id')
        print(values)
        print('childs ',self.child_ids)
        unlink_addresses = []
        has_delivery = False
        primary_count = 0
        if values.get('child_ids'): 
          for child_to_update in values.get('child_ids'):
               if child_to_update[0] == 1:
                   adres = partners.search([('id','=',child_to_update[1])])
                   adres.write(child_to_update[2])
               elif child_to_update[0] == 2:
                   unlink_addresses.append(child_to_update[1])
               elif child_to_update[0] == 0:
                   adr = child_to_update[2]
                   if adr.get('type') == 'delivery':
                       has_delivery = True
                       if adr.get('primary_address'):
                           primary_count += 1

        str_error = ''
        print('childs ',self.child_ids)
        addresses = self.child_ids
        print('adr ', addresses)
        for address in addresses:
            adr_to_check = address
            if address.id in unlink_addresses:
                continue
            if address.type == 'delivery':
                has_delivery = True
                if address.primary_address:
                    primary_count += 1

        if has_delivery and primary_count != 1:
            str_error += ' For the partner must be one delivery address with the primary address set'
            not_allowed = True

        if not_allowed:
            raise UserError(str_error)
        return super(PrimaryAddressForPartner,self).write(values)
