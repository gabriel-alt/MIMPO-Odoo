""" Purchase Orders """
from odoo import api, models

class PurchaseOrder(models.Model):
    """ Inherit Object purchase.order """
    _inherit = 'purchase.order'

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        res['sir_id'] = self.sir_id.id
        return res

class PurchaseOrderLine(models.Model):
    """ Inherit Object purchase.order.line """
    _inherit = 'purchase.order.line'

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        res['sir_id'] = self.sir_id.id
        return res

    @api.onchange('sir_id')
    def _onchange_sir_id(self):
        """ Set analytic_distribution on purchase line when change SIR """
        if self.sir_id:
            analytic_distribution = {str(self.sir_id.account_analytic_id.id):100}
            self.analytic_distribution = analytic_distribution
