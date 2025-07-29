""" Account Move """
from odoo import models, fields, api, _
from odoo.addons.web.controllers.utils import clean_action

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    bank_global_deposit_ids = fields.One2many(
        'account.bank.global.deposit', 'st_line_id',
        string="Bank Global Deposit", readonly=True, copy=False)

    @api.onchange('global_deposit')
    def _onchange_global_deposit(self):
        if self.global_deposit:
            self.sir_id = False

class BankRecWidget(models.Model):
    _inherit = "bank.rec.widget"

    global_deposit = fields.Boolean(
        related='st_line_id.move_id.global_deposit',
        depends=['st_line_id'],
    )

    def _action_trigger_matching_rules(self):
        res = super(BankRecWidget, self)._action_trigger_matching_rules()
        if self.move_id.global_deposit:
            reconcile_models = self.env['account.reconcile.model'].search([
                ('company_id', '=', self.company_id.id),
                ('account_model', '=', 'fondo'),
            ])
            if reconcile_models:
                self._process_todo_command(
                    'select_reconcile_model_button', [str(reconcile_models[0].id)])
        return res

    def _create_bank_global_deposit(self):
        """ Create Bank Global Deposit """
        self.env['account.bank.global.deposit'].create({
            'st_line_id': self.st_line_id.id,
            'line_ids': [(6, 0, [])]
        })

    def button_validate(self, async_action=False):
        """ Inherit Button Validate """
        res = super(BankRecWidget, self).button_validate(async_action=async_action)
        if self.st_line_id and self.st_line_id.global_deposit and self.partner_id:
            self._create_bank_global_deposit()
        return res

    def button_open_global_deposit_form(self):
        self.ensure_one()
        if self.st_line_is_reconciled and self.st_line_id.global_deposit and \
            self.st_line_id.bank_global_deposit_ids:
            action = {
                'type': 'ir.actions.act_window',
                'context': {},
                'res_model': 'account.bank.global.deposit',
            }
            if len(self.st_line_id.bank_global_deposit_ids) == 1:
                action.update({
                    'view_mode': 'form',
                    'res_id': self.st_line_id.bank_global_deposit_ids[0].id,
                })
            else:
                action.update({
                    'view_mode': 'list,form',
                    'domain': [('id', 'in', self.st_line_id.bank_global_deposit_ids.ids)],
                })
            self.next_action_todo = clean_action(action, self.env)
        else:
            self.next_action_todo = {'type': 'refresh_statement_line'}
