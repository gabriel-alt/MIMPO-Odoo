""" Account Payment """
from odoo import models, fields, api

class AccountPayment(models.Model):
    """ Inherit Account Payment """
    _inherit = 'account.payment'

    sir_id = fields.Many2one('sir.ref',string='Referencia SIR')

    @api.model_create_multi
    def create(self, vals_list):
        """ Extend function create payment """
        res = super(AccountPayment, self).create(vals_list)
        for pay in res:
            pay.move_id.write({'sir_id': pay.sir_id.id})
            analytic_distribution = {str(pay.sir_id.account_analytic_id.id):100}
            pay.move_id.line_ids.write({
                'sir_id': pay.sir_id.id,
                'analytic_distribution': analytic_distribution
                })
        return res

    def write(self, vals):
        """ Extend function write payment """
        res = super().write(vals)
        if vals.get('sir_id'):
            for pay in self:
                sir_id = self.env['sir.ref'].search([('id','=', vals.get('sir_id'))])
                analytic_distribution = {str(sir_id.account_analytic_id.id):100}
                pay.move_id.write({'sir_id': vals.get('sir_id')})
                pay.move_id.line_ids.write({
                    'sir_id': vals.get('sir_id'),
                    'analytic_distribution': analytic_distribution
                    })
        return res
