""" Account Journal """
from odoo import api, fields, models, _

class AccountJournal(models.Model):
    """ Inherit Account Journal """
    _inherit = 'account.journal'

    down_payment_journal = fields.Boolean(string='Down Payment')

    @api.depends('type', 'down_payment_journal')
    def _compute_default_account_type(self):
        super(AccountJournal, self)._compute_default_account_type()
        for journal in self:
            if journal.down_payment_journal and journal.type == 'sale':
                journal.default_account_type = 'liability_current'

    @api.onchange('down_payment_journal')
    def _onchange_down_payment_journal(self):
        if self.default_account_id:
            self.default_account_id = False

