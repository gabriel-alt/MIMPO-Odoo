""" Account Move Line """
from odoo import models

class AccountMoveLine(models.Model):
    """ Inherit Account Move Line """
    _inherit = 'account.move.line'

    def remove_move_reconcile(self):
        """ Undo a reconciliation """

        res = super(AccountMoveLine, self).remove_move_reconcile()
        if self.move_id.statement_line_id.sir_id:
            self.sir_id = False
            if self.move_id.sir_id:
                self.move_id.sir_id = False
        return res
