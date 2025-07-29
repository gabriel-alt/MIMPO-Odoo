# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class AccountBankGlobalDeposit(models.Model):
    _name = 'account.bank.global.deposit'
    _description = 'Account Bank Global Deposit'

    st_line_id = fields.Many2one(
        comodel_name='account.bank.statement.line',
        required=True)
    partner_id = fields.Many2one(
        related='st_line_id.partner_id', readonly=True, store=True)
    move_id = fields.Many2one(
        related='st_line_id.move_id', readonly=True)
    name = fields.Char(
        related='st_line_id.move_id.name', readonly=True)
    amount = fields.Monetary(
        related='st_line_id.amount', readonly=True, string='Balance')
    currency_id = fields.Many2one(
        related='st_line_id.currency_id', readonly=True, store=True)
    foreign_currency_id = fields.Many2one(
        related='st_line_id.foreign_currency_id', readonly=True, store=True)
    amount_currency = fields.Monetary(
        related='st_line_id.amount_currency', currency_field='foreign_currency_id',
        readonly=True, string='Amount in Currency')
    date = fields.Date(
        related='st_line_id.date', readonly=True, store=True)
    line_ids = fields.One2many(
        'account.bank.global.deposit.line', 'global_deposit_id',
        string='Lines')
    available_amount = fields.Monetary(
        string='Available balance', compute='_compute_amount_deposit')
    assigned_amount = fields.Monetary(
        string='Assigned balance', compute='_compute_amount_deposit')
    available_sir_ids = fields.Many2many(
        'sir.ref', 'account_global_deposit_sir_ref_rel',
        'global_deposit_id', 'sir_id', compute="_compute_available_sir_ids")

    @api.depends('st_line_id.amount', 'line_ids.assigned_amount')
    def _compute_amount_deposit(self):
        for this in self:
            assigned_amount = sum(this.line_ids.mapped('assigned_amount'))
            this.update({
                'available_amount': this.amount - assigned_amount,
                'assigned_amount': assigned_amount,
            })

    def _compute_available_sir_ids(self):
        for this in self:
            domain = []
            if this.partner_id:
                if this.partner_id.partner_ref:
                    domain = [
                        ('state', '=', 'open'),
                        '|', ('customer', '=', str(this.partner_id.partner_ref)),
                        ('partner_id', '=', this.partner_id.id)]
                else:
                    domain = [
                        ('state', '=', 'open'),
                        ('partner_id', '=', this.partner_id.id)]
            sir_ids = self.env['sir.ref'].search(domain)
            this.update({'available_sir_ids': [(6, 0, sir_ids.ids)]})


class AccountBankGlobalDepositLine(models.Model):
    _name = 'account.bank.global.deposit.line'
    _description = 'Account Bank Global Deposit Line'

    global_deposit_id = fields.Many2one(
        'account.bank.global.deposit', string='Global Deposit',
        index=True, required=True, ondelete='cascade')
    record_date = fields.Date(default=fields.Date.context_today)
    sir_id = fields.Many2one('sir.ref', string="Referencia SIR", required=True)
    currency_id = fields.Many2one(
        related='global_deposit_id.currency_id', readonly=True, store=True)
    assigned_amount = fields.Monetary()
    foreign_currency_id = fields.Many2one(
        comodel_name='res.currency', string="Foreign Currency",)
    amount_currency = fields.Monetary(
        compute='_compute_amount_currency', inverse='_inverse_amount_currency',
        store=True, readonly=False,
        string="Amount in Currency",
        currency_field='foreign_currency_id',)
    created_move_id = fields.Many2one(
        'account.move', string="Created Move", readonly=True)   
    trusted_fund_move_ids = fields.Many2many(
        "account.move", "account_move_global_deposit_line_rel",
        "global_deposit_line_id", "move_id")

    @api.constrains('assigned_amount', 'amount_currency', 'currency_id', 'foreign_currency_id')
    def validate_assigned_amount(self):
        for record in self:
            if record.assigned_amount <= 0:
                raise ValidationError(_("Please set a positive Assigned Amount."))
            if record.foreign_currency_id and record.amount_currency <= 0:
                raise ValidationError(_("Please set a positive Amount in Currency."))

    @api.depends('foreign_currency_id', 'record_date', 'assigned_amount')
    def _compute_amount_currency(self):
        for st_line in self:
            if not st_line.foreign_currency_id:
                st_line.amount_currency = False
            elif st_line.record_date and not st_line.amount_currency:
                # only convert if it hasn't been set already
                bank_move_id = st_line.global_deposit_id.move_id
                st_line.amount_currency = st_line.currency_id._convert(
                    from_amount=st_line.assigned_amount,
                    to_currency=st_line.foreign_currency_id,
                    company=bank_move_id.company_id,
                    date=st_line.record_date,
                )

    @api.onchange('amount_currency', 'currency_id')
    def _inverse_amount_currency(self):
        for line in self:
            if line.currency_id == line.foreign_currency_id and \
                line.assigned_amount != line.amount_currency:
                line.assigned_amount = line.amount_currency
            elif line.currency_id != line.foreign_currency_id and line.amount_currency:
                bank_move_id = line.global_deposit_id.move_id
                new_assigned_amount = line.foreign_currency_id._convert(
                    from_amount=line.amount_currency,
                    to_currency=line.currency_id,
                    company=bank_move_id.company_id,
                    date=line.record_date,
                )
                if new_assigned_amount != line.assigned_amount:
                    line.assigned_amount = new_assigned_amount

    def create_journal_entry_deposit_sir(self):
        self.ensure_one()
        if not self.assigned_amount:
            raise UserError(_('Please set Assigned Amount for this line'))
        if self.global_deposit_id.available_amount < 0.0:
            amount_i = self.global_deposit_id.available_amount + self.assigned_amount
            amount_text = self.currency_id.with_context(
                lang=self.env.user.lang or 'es_ES').format(amount_i)
            raise UserError(_('You are trying to use more balance than available, remaining balance is %s' %(amount_text)))
        bank_move_id = self.global_deposit_id.move_id
        non_bank_line_id = bank_move_id.line_ids.filtered(
            lambda l: l.account_id.account_type not in ['asset_cash', 'off_balance'])
        journal_id = bank_move_id.company_id.global_deposit_journal_id or False
        if not journal_id:
            journal_id = self.env['account.journal'].search([
                ('company_id', '=', bank_move_id.company_id.id),
                ('type', '=', 'general')], limit=1)
        currency_id = self.currency_id
        amount = self.assigned_amount
        if self.foreign_currency_id:
            currency_id = self.foreign_currency_id
            amount = self.amount_currency
        vals = {
            'journal_id': journal_id.id,
            'date': self.record_date,
            'ref': 'Global Deposit %s' %(self.sir_id.display_name),
            'partner_id': self.global_deposit_id.partner_id.id or False,
            'currency_id': currency_id.id,
            'line_ids' : [
                (0, 0, {
                    'account_id': non_bank_line_id[0].account_id.id,
                    'amount_currency': amount,
                    # 'debit': self.assigned_amount,
                    'quantity': 1.0,
                    'currency_id': currency_id.id,
                    'name': non_bank_line_id[0].name,
                    'partner_id': self.global_deposit_id.partner_id.id or False,
                }),
                (0, 0, {
                    'account_id': non_bank_line_id[0].account_id.id,
                    'amount_currency': -1 * amount,
                    # 'credit': self.assigned_amount,
                    'quantity': 1.0,
                    'currency_id': currency_id.id,
                    'name': 'Global Deposit %s' %(self.sir_id.display_name),
                    'partner_id': self.global_deposit_id.partner_id.id or False,
                    'sir_id': self.sir_id.id,
                    'analytic_distribution': {str(self.sir_id.account_analytic_id.id):100}
                })
            ]
        }
        move_id = self.env['account.move'].create(vals)
        self.write({'created_move_id': move_id.id})
        action = {
            'type': 'ir.actions.act_window',
            'context': {},
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': move_id.id,
        }
        return action

    def action_show_created_move(self):
        self.ensure_one()
        if not self.created_move_id:
            raise UserError(_('Counter Journal Entry not created yet'))
        action = {
            'type': 'ir.actions.act_window',
            'context': {},
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.created_move_id.id,
        }
        return action

    def button_create_open_journal(self):
        if self.created_move_id:
            return self.action_show_created_move()
        else:
            return self.create_journal_entry_deposit_sir()

    def unlink(self):
        for this in self:
            if this.created_move_id:
                raise UserError(_('You cannot delete line already have Journal Entry'))
        return super(AccountBankGlobalDepositLine, self).unlink()
