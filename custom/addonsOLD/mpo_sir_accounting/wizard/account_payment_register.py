""" Account Payment Register """
from odoo import api, models, fields, _
from odoo.exceptions import UserError

class AccountPaymentRegisterSir(models.TransientModel):
    """ New object Account Payment Register SIR"""
    _name = 'account.payment.register.sir'
    _description = 'Account Payment Register SIR'

    pay_reg_id = fields.Many2one('account.payment.register')
    sir_line_ids = fields.Many2many(
        'account.move.line', string='SIR Bill Line', required=True)
    sir_id = fields.Many2one(
        'sir.ref', string='Referencia SIR')
    amount = fields.Float()

class AccountPaymentRegister(models.TransientModel):
    """ Inherit object Account Payment Register """
    _inherit = 'account.payment.register'

    bill_multi_sir = fields.Boolean()
    multi_sir_ids = fields.One2many(
        'account.payment.register.sir', 'pay_reg_id', string='Multi SIR',
        store=True, readonly=False,
        compute='_compute_multi_sir_ids')

    def _get_price_amount(self, amount=0.0):
        if not amount:
            return amount
        if self.source_currency_id == self.currency_id:
            return amount
        return self.source_currency_id._convert(
            amount, self.currency_id, self.company_id, self.payment_date,)

    @api.depends('amount', 'line_ids', 'bill_multi_sir')
    def _compute_multi_sir_ids(self):
        for this in self:
            if this.amount and this.line_ids and this.bill_multi_sir:
                move_id = this.line_ids[0].move_id
                invoice_lines = move_id.invoice_line_ids
                recon_sir = {}
                if move_id.payment_state == 'partial':
                    for out in move_id._get_all_reconciled_invoice_partials():
                        if out['aml'].sir_id:
                            if out['aml'].sir_id.id in recon_sir:
                                recon_sir[out['aml'].sir_id.id] += out['amount']
                            else:
                                recon_sir[out['aml'].sir_id.id] = out['amount']
                sir_lines = {}
                for line in invoice_lines:
                    price_amount = this._get_price_amount(amount=line.price_total)
                    if line.sir_id:
                        if line.sir_id.id in recon_sir:
                            price_amount -= recon_sir[line.sir_id.id]
                        if line.sir_id.id in sir_lines:
                            sir_lines[line.sir_id.id][
                                'amount'] += price_amount
                            sir_lines[line.sir_id.id][
                                'sir_line_ids'][0][2].append(line.id)
                        else:
                            sir_lines[line.sir_id.id] = {
                                'sir_id': line.sir_id.id,
                                'sir_line_ids': [(6, 0, line.ids)],
                                'amount' : price_amount
                            }
                    elif line.move_id.sir_id:
                        if line.move_id.sir_id.id in recon_sir:
                            price_amount -= recon_sir[line.move_id.sir_id.id]
                        if line.move_id.sir_id.id in sir_lines:
                            sir_lines[line.move_id.sir_id.id][
                                'amount'] += price_amount
                            sir_lines[line.move_id.sir_id.id][
                                'sir_line_ids'][0][2].append(line.id)
                        else:
                            sir_lines[line.move_id.sir_id.id] = {
                                'sir_id': line.move_id.sir_id.id,
                                'sir_line_ids': [(6, 0, line.ids)],
                                'amount' : price_amount
                            }
                multi_sir_ids = [(5, 0, 0)]
                for k, v in sir_lines.items():
                    multi_sir_ids.append((0, 0, v))
                this.multi_sir_ids = multi_sir_ids

    def _create_payments(self):
        if self.bill_multi_sir and self.multi_sir_ids:
            total_amount = sum(self.multi_sir_ids.mapped('amount'))
            if self.currency_id.compare_amounts(self.amount, total_amount) != 0:
                raise UserError("Total Amount in SIR Line is not same with Amount")
            self = self.with_context(skip_account_move_synchronization=True)
        res = super(AccountPaymentRegister, self)._create_payments()
        for data in res:
            move_ids = data.reconciled_invoice_ids + data.reconciled_bill_ids
            for move in move_ids:
                sir_id = False
                if move.sir_id:
                    sir_id = move.sir_id
                else:
                    for aml in move.invoice_line_ids:
                        if not sir_id:
                            sir_id = aml.sir_id
                if not data.sir_id and sir_id:
                    if move.sir_id:
                        data.sir_id = sir_id.id
                        data.move_id.sir_id = sir_id.id
                    for payment_line in data.move_id.line_ids:
                        analytic_distribution = {str(sir_id.account_analytic_id.id):100}
                        if not payment_line.sir_id:
                            payment_line.sir_id = sir_id.id
                        if not payment_line.analytic_distribution:
                            payment_line.analytic_distribution = analytic_distribution
        return res

    def _init_payments(self, to_process, edit_mode=False):
        payments = super(AccountPaymentRegister, self)._init_payments(
            to_process, edit_mode=edit_mode)
        if not self.bill_multi_sir:
            return payments
        for payment in payments:
            update_line = []
            pay_line = False
            payable_vals = {}
            for line in payment.move_id.line_ids:
                if line.account_type in ['asset_receivable', 'liability_payable']:
                    pay_line = line
                    payable_vals = {
                        'name': line.name,
                        'date_maturity': line.date_maturity,
                        'amount_currency': 0.0,
                        'currency_id': line.currency_id.id,
                        'debit': 0.0,
                        'credit': 0.0,
                        'partner_id': line.partner_id.id,
                        'account_id': line.account_id.id,
                        'currency_rate': line.currency_rate,
                    }
            first_line = True
            for ml in self.multi_sir_ids:
                if not ml.amount:
                    continue
                analytic_distribution = {}
                if ml.sir_id.account_analytic_id:
                    analytic_distribution = {
                        str(ml.sir_id.account_analytic_id.id):100}
                amount_currency = ml.amount
                if pay_line.credit:
                    amount_currency = -1 * ml.amount
                if pay_line.currency_id != pay_line.company_id.currency_id:
                    amount_currency = pay_line.currency_id.round(
                        amount_currency * pay_line.currency_rate)
                if first_line:
                    update_vals = {
                        'sir_id': ml.sir_id.id,
                        'analytic_distribution': analytic_distribution,
                        'debit' : pay_line.debit and ml.amount or 0.0,
                        'credit' : pay_line.credit and ml.amount or 0.0,
                        'amount_currency': amount_currency
                    }
                    update_line.append((1, pay_line.id, update_vals))
                else:
                    update_vals = payable_vals.copy()
                    update_vals['sir_id'] = ml.sir_id.id
                    update_vals['analytic_distribution'] = analytic_distribution
                    update_vals['debit'] = pay_line.debit and ml.amount or 0.0
                    update_vals['credit'] = pay_line.credit and ml.amount or 0.0
                    update_vals['amount_currency'] = amount_currency
                    update_line.append((0, 0, update_vals))
                first_line = False
            move_id = line.move_id.with_context(skip_invoice_sync=True)
            move_id.with_context(skip_account_move_synchronization=True).write({'line_ids': update_line})
        return payments

