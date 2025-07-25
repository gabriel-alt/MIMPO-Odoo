from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_purchase_order_data(self, company, company_partner):
        res = super(SaleOrder, self)._prepare_purchase_order_data(
            company, company_partner)
        if self.sir_id:
            res.update({'sir_id': self.sir_id.id,})
        if self.custom_broker_id:
            res.update({'custom_broker_id': self.custom_broker_id.id})
        return res
