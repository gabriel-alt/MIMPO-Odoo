""" Account Move """
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    """ Inherit Account Move """
    _inherit = 'account.move'

    global_deposit = fields.Boolean(copy=False)
    global_deposit_line_ids = fields.Many2many(
        "account.bank.global.deposit.line",
        "account_move_global_deposit_line_rel",
        "move_id", "global_deposit_line_id",
        compute="_compute_trusted_fund_balance", store=True)

    @api.depends('sir_id', 'date', 'total_expense', 'amount_total',
                 'state', 'currency_id', 'total_expense_currency')
    def _compute_trusted_fund_balance(self):
        """ Replace Compute Balance of trusted fund amount """
        for move in self:
            tf_line = self.env['account.bank.statement.line'].sudo()
            gl_line = []
            tr_bal = 0.0
            if move.sir_id and move.state != 'cancel' \
                    and move.move_type in ('out_invoice', 'out_refund'):
                domain = [('sir_id', '=', move.sir_id.id),
                          ('move_id.company_id', '=', move.company_id.id)]
                st_line = self.env['account.bank.statement.line'].sudo().search(domain)
                for line in st_line:
                    # skip if bank statement already linked to other invoice
                    if line.trusted_fund_move_ids \
                            and line.trusted_fund_move_ids.filtered(
                                lambda r, m=move: r.state != 'cancel' and r != m._origin):
                        continue
                    # skip non trusted account
                    if all(not sl.account_id.trust_fund for sl in line.move_id.line_ids):
                        continue
                    tf_line |= line
                    if line.currency_id != move.currency_id:
                        rate = self.env['res.currency']._get_conversion_rate(
                            from_currency=line.currency_id,
                            to_currency=move.currency_id,
                            company=move.company_id,
                            date=move.invoice_date or move.date \
                                or fields.Date.context_today(line))
                        tr_bal += abs(move.currency_id.round(
                            line.amount / rate))
                    else:
                        tr_bal += abs(line.amount)
                global_deposit_line = self.env[
                    'account.bank.global.deposit.line'].sudo().search([
                        ('sir_id', '=', move.sir_id.id),
                        ('created_move_id', '!=', False)
                    ])
                for gdl in global_deposit_line:
                    # skip if global deposit line already linked to other invoice
                    if gdl.created_move_id.state != 'posted':
                        continue
                    if gdl.trusted_fund_move_ids \
                            and gdl.trusted_fund_move_ids.filtered(
                                lambda r, m=move: r.state != 'cancel' and r != m._origin):
                        continue
                    if all(not sl.account_id.trust_fund for sl in gdl.created_move_id.line_ids):
                        continue
                    gl_line.append(gdl.id)
                    gdl_currency = gdl.currency_id
                    gdl_amount = abs(gdl.assigned_amount)
                    if gdl.foreign_currency_id:
                        gdl_currency = gdl.foreign_currency_id
                        gdl_amount = abs(gdl.amount_currency)
                    if gdl_currency != move.currency_id:
                        tr_bal += gdl_currency._convert(
                            from_amount=gdl_amount,
                            to_currency=move.currency_id,
                            company=move.company_id,
                            date=move.invoice_date or move.date \
                                or fields.Date.context_today()
                        )
                    else:
                        tr_bal += gdl_amount
            # remaining = tr_bal - sum(move.invoice_line_ids.filtered(
            #     lambda r: not r.cga_line and r.display_type == 'product').mapped(
            #         'price_total'))
            move.update({
                'remaining_trusted_fund_balance': move.currency_id.round(
                    tr_bal - move.total_expense_currency),
                'trusted_fund_balance': tr_bal,
                'trusted_fund_statement_line_ids': [(6, 0, tf_line.ids)],
                'global_deposit_line_ids': [(6, 0, gl_line)]})

    def _get_new_expense_items(self, type_sign=1):
        items = super()._get_new_expense_items(type_sign=type_sign)
        if not self.global_deposit_line_ids:
            return items
        for gdl in self.global_deposit_line_ids:
            if all(not sl.account_id.trust_fund for sl in gdl.created_move_id.line_ids):
                msg = "Please define account for trust fund in " \
                    f"the bank stamement line {gdl.global_deposit_id.st_line_id.payment_ref}"
                raise ValidationError(_(msg))
            filter_line = gdl.created_move_id.line_ids.filtered(
                lambda l: l.account_id.trust_fund)
            account_id = filter_line and filter_line[0].account_id or False
            if not account_id:
                raise ValidationError(_('In Global Deposit cannot find Trust fund account'))
            gdl_currency = gdl.currency_id
            gdl_amount = abs(gdl.assigned_amount)
            if gdl.foreign_currency_id:
                gdl_currency = gdl.foreign_currency_id
                gdl_amount = abs(gdl.amount_currency)
            if gdl_currency != self.currency_id:
                tr_bal = gdl_currency._convert(
                    from_amount=gdl_amount,
                    to_currency=self.currency_id,
                    company=self.company_id,
                    date=self.invoice_date or self.date \
                        or fields.Date.context_today()
                )
            else:
                tr_bal = gdl_amount
            tf_line = {'account_id': account_id.id,
                       'trust_fund_account_id': account_id.id,
                       'name': filter_line[0].name,
                       'partner_id': self.partner_id.id,
                       'analytic_distribution': {str(self.sir_id.account_analytic_id.id):100},
                       'quantity': 1.0,
                       'price_unit': type_sign * -1 * tr_bal,
                       'tax_ids': [(6, 0, [])],
                    #    'debit': -1 * tr_bal,
                    #    'credit': 0.0,
                    #    'balance': type_sign * -1 * tr_bal,
                       'currency_id': self.currency_id.id,
                       'cga_line': True,
                       'expense_bill_currency_id': gdl_currency.id,
                       'expense_amount_currency': type_sign * -1 * gdl_amount,
                    #    'display_type': 'product'
                       }
            items.append((0, 0, tf_line))
        return items
