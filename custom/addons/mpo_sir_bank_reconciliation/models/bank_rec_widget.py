""" Bank Rec Widget """
from odoo import api, models

class BankRecWidget(models.Model):
    """ Inherit Bank Rec Widget """
    _inherit = "bank.rec.widget"

    def update_statement_line_sir(self):
        """ Update Bank Statement Line Sir Reference """

        if self.st_line_id.sir_id:
            analytic_distribution = False
            self.st_line_id.move_id.sir_id = self.st_line_id.sir_id.id
            if self.st_line_id.sir_id.account_analytic_id:
                analytic_distribution = {str(self.st_line_id.sir_id.account_analytic_id.id):100}
            for line in self.st_line_id.line_ids:
                vals = {'sir_id': self.st_line_id.sir_id.id}
                if line.account_id.account_type != 'asset_cash':
                    vals.update({'analytic_distribution': analytic_distribution})
                line.write(vals)

    def button_validate(self, async_action=False):
        """ Inherit Button Validate """

        self.ensure_one()
        res = super(BankRecWidget, self).button_validate(async_action=async_action)
        self.update_statement_line_sir()
        return res

    # @api.model
    # def js_action_reconcile_st_line(self, st_line_id, params):
    #     """ Modify Function Reconcile (Validate) on Bank Statement to set SIR Reference """
    #     res = super().js_action_reconcile_st_line(st_line_id, params)
    #     st_line = self.env[
    #         'account.bank.statement.line'].browse(st_line_id)
    #     if st_line.sir_id:
    #         analytic_distribution = False
    #         move_id = st_line.move_id
    #         move_id.sir_id = st_line.sir_id.id
    #         if st_line.sir_id.account_analytic_id:
    #             analytic_distribution = {str(st_line.sir_id.account_analytic_id.id):100}
    #         for line in move_id.line_ids:
    #             line.sir_id = st_line.sir_id.id
    #             line.analytic_distribution = analytic_distribution
    #     return res
