""" Sale Orders """
from odoo import api, fields, models

class SaleOrder(models.Model):
    """ Inherit Object sale.order """
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['sir_id'] = self.sir_id.id
        return res

class SaleOrderLine(models.Model):
    """ Inherit Object sale.order """
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        res = super()._prepare_invoice_line(**optional_values)
        res.update(sir_id=self.sir_id.id)
        return res

    @api.onchange('sir_id')
    def _onchange_sir_id(self):
        """ Set analytic_distribution on sale line when change SIR """
        if self.sir_id:
            analytic_distribution = {str(self.sir_id.account_analytic_id.id):100}
            self.analytic_distribution = analytic_distribution
