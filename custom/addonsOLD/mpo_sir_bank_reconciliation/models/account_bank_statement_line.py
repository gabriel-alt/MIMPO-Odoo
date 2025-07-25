""" Account Bank Statement Line """
from odoo import models, fields

class AccountBankStatementLine(models.Model):
    """ Inherit Account Bank Statement Line """
    _inherit = 'account.bank.statement.line'

    sir_id = fields.Many2one('sir.ref', string="Referencia SIR")
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          related='sir_id.account_analytic_id',
                                          string='Analítica')
    custom_broker_ids = fields.Many2many('res.partner', string='Corresponsales')
