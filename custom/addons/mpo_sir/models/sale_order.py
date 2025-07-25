# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sir_id = fields.Many2one('sir.ref', string='Referencia SIR')
    msa_type = fields.Selection(
        selection=[('qo', 'Cotización'), 
                   ('ar', 'Previa solicitud'),],
        string=_('MSA')
    )

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
        """ Set SIR on sale line when update header SIR ID """

        for order in self:
            if order.sir_id:
                partner = self.env['res.partner'].search_read(
                    domain=[('partner_ref', '=', order.sir_id.customer)], fields=['id'], limit=1)
                if partner:
                    order.update({'partner_id': partner[0].get('id')})
                for line in self.order_line:
                    analytic_distribution = {str(order.sir_id.account_analytic_id.id):100}
                    line.update({'sir_id': order.sir_id.id,
                                 'analytic_distribution': analytic_distribution})


class SaleOrderLine(models.Model):
    """ Inherit Object sale.order """
    _inherit = 'sale.order.line'

    sir_id = fields.Many2one('sir.ref',string='Referencia SIR')
