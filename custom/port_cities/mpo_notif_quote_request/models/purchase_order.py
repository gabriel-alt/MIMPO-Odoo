""" Purchase Order """
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    """ Inherit Purchase Order """
    _inherit = 'purchase.order'

    @api.model_create_multi
    def create(self, vals_list):
        orders = super(PurchaseOrder, self).create(vals_list)
        for order in orders:
            quote_template_id = False
            for line in order.order_line:
                if line.product_id and \
                    line.product_id.notif_quote_template_id and (
                    line.product_id.notif_quote_template_id.email_to or \
                    line.product_id.notif_quote_template_id.partner_to):
                    quote_template_id = line.product_id.notif_quote_template_id
                    break
            if quote_template_id:
                quote_template_id.send_mail(
                    order.id,
                    force_send=True,
                    raise_exception=False,)
        return orders

    def get_to_purchase_order_url(self):
        self.ensure_one()
        menu_id = self.env.ref(
            'purchase.menu_purchase_rfq',
            raise_if_not_found=False)
        if not menu_id:
            return False
        return '/web?db=%s#id=%s&view_type=list&model=%s&menu_id=%s' % (
            self.env.cr.dbname, self.id, 'purchase.order', menu_id.id)
