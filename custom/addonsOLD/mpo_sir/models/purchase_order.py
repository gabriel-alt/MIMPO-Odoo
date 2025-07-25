# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sir_id = fields.Many2one('sir.ref',string='Referencia SIR')

    # @api.onchange('partner_id','sir_id')
    # def _onchange_sir_id_domain(self):
    #     for rec in self:
    #         domain = [('state', '=', 'open')]
    #         if rec.partner_id.partner_ref:
    #             partner_ref = rec.partner_id.partner_ref
    #             domain = [('customer', '=', str(partner_ref)),
    #                   ('state', '=', 'open')]
    #         return {'domain': {'sir_id': domain}}

    @api.onchange('sir_id')
    def _onchange_sir_id(self):
        """ Set SIR on purchase line when update header SIR ID """

        for order in self:
            if order.sir_id:
                for line in order.order_line:
                    analytic_distribution = {str(order.sir_id.account_analytic_id.id):100}
                    line.update({'sir_id': order.sir_id.id,
                                 'analytic_distribution': analytic_distribution})


class PurchaseOrderLine(models.Model):
    """ Inherit Object purchase.order """
    _inherit = 'purchase.order.line'

    sir_id = fields.Many2one('sir.ref',string='Referencia SIR')
