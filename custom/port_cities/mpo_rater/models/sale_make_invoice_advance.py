# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def _create_invoices(self, sale_orders):
        res = super(SaleAdvancePaymentInv, self)._create_invoices(sale_orders)
        if sale_orders.house_id:
            res.house_id = sale_orders.house_id
        if sale_orders.sir_id:
            res.sir_id = sale_orders.sir_id
        if sale_orders.operation_type:
            res.operation_type = sale_orders.operation_type
        if sale_orders.rate_id:
            res.rate_id = sale_orders.rate_id