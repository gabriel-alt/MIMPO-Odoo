""" Account Bank Statement Line """
from odoo import models, fields

class AccountBankStatementLine(models.Model):
    """ Inherit Account Bank Statement Line """

    _inherit = 'account.bank.statement.line'

    trusted_fund_move_ids = fields.Many2many(
        "account.move", "account_move_trusted_fund_statement_line_rel",
        "statement_line_id", "move_id")
