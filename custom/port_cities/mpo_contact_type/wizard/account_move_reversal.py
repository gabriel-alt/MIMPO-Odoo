""" Account Move Reversal """
from odoo import models


class AccountMoveReversal(models.TransientModel):
    """ Inherit Account Move Reversal """

    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        """ Inherit Prepare Default Reversal """

        res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        # add vals custom broker
        res.update({'custom_broker_id': move.custom_broker_id.id})
        return res
