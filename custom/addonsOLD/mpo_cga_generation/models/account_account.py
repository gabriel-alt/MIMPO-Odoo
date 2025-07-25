""" Account Account """
from odoo import models, fields, api


class AccountAccount(models.Model):
    """ Inherit Account Account """

    _inherit = 'account.account'

    trust_fund = fields.Boolean("Fondo Confiado")


class AccountReconcileModel(models.Model):
    """ Inherit Account Reconcile Model """
    _inherit = 'account.reconcile.model'

    fondo_confiado = fields.Boolean()
    account_model = fields.Selection([
        ('fondo', 'Fondo Confiado'), ('deposit', 'Depósito en garantía'),
        ('down_payment', 'Anticipo')],
        string='Model Type')

class BankRecWidget(models.Model):
    _inherit = "bank.rec.widget"

    def _action_select_reconcile_model(self, reco_model):
        res = super(BankRecWidget, self)._action_select_reconcile_model(reco_model)
        if reco_model.account_model and self.company_id:
            for line in self.line_ids:
                if line.partner_id and line.flag in [
                    'auto_balance', 'manual', 'new_aml']:
                    account_id = False
                    if reco_model.account_model == 'fondo':
                        account_id = line.partner_id.with_company(
                            self.company_id).property_account_fondo_confiado_id
                    elif reco_model.account_model == 'deposit':
                        account_id = line.partner_id.with_company(
                            self.company_id).property_account_deposit_id
                    elif reco_model.account_model == 'down_payment':
                        account_id = line.partner_id.with_company(
                            self.company_id).property_account_down_payment_id
                    if account_id:
                        line.account_id = account_id
        # elif not reco_model.fondo_confiado and self.company_id:
        #     for line in self.line_ids:
        #         if line.partner_id and line.flag in [
        #             'auto_balance', 'manual', 'new_aml'] and line.source_aml_id:
        #             line.account_id = line.source_aml_id.account_id
        return res

# class BankRecWidgetLine(models.Model):
#     _inherit = "bank.rec.widget.line"

#     @api.depends('source_aml_id')
#     def _compute_account_id(self):
#         super(BankRecWidgetLine, self)._compute_account_id()
#         eco_model_id = self.env['account.reconcile.model']
#         for line in self:
#             if line.flag == 'liquidity' and line.partner_id:
#                 fondo_account_id = line.partner_id.with_company(
#                     line.wizard_id.company_id).property_account_fondo_confiado_id
#                 if not fondo_account_id:
#                     continue
#                 eco_model_id = self.env['account.reconcile.model'].search([
#                     ('rule_type', '=', 'writeoff_button'),
#                     ('company_id', '=', line.wizard_id.company_id.id),
#                     '|',
#                     ('match_journal_ids', '=', False),
#                     ('match_journal_ids', '=',
#                     line.wizard_id.st_line_id.journal_id.id),
#                 ], limit=1)
#                 if eco_model_id and eco_model_id[0].fondo_confiado:
#                     line.account_id = fondo_account_id

#     @api.depends('source_aml_id')
#     def _compute_currency_id(self):
#         super(BankRecWidgetLine, self)._compute_currency_id()
#         for line in self:
#             if not line.currency_id:
#                 line.currency_id = line.wizard_id.transaction_currency_id