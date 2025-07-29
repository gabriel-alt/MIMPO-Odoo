from odoo import models,fields,api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    transport_request_id = fields.Many2one(
        'transport.request', string="Request Number")
    request_purchase = fields.Boolean("Transport Request")
    load_order_id = fields.Many2one(
        'load.order', string="Load Order")

    @api.model_create_multi
    def create(self, vals_list):
        order_ids = super(SaleOrder, self).create(vals_list)
        for order in order_ids:
            if order.load_order_id:
                order.load_order_id.write({
                    'sale_id': order.id})
        return order_ids

