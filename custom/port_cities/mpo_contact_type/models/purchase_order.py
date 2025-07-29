""" Purchase Order """
from odoo import fields, models


class PurchaseOrder(models.Model):
    """ Inherit Purchase Order """

    _inherit = 'purchase.order'

    def contact_type_domain(self):
        return [('contact_type_id','=',self.env.ref('mpo_contact_type.data_contact_type_custom_broker').id)]

    custom_broker_id = fields.Many2one("res.partner", string="Corresponsal", domain=contact_type_domain)

    def _prepare_invoice(self):
        """ Inherit Prepare Invoice """

        res = super(PurchaseOrder, self)._prepare_invoice()
        # add vals custom broker
        res.update({'custom_broker_id': self.custom_broker_id.id})
        return res
