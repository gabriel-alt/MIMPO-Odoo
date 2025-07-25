from odoo import models, fields, api
from odoo.tools import float_is_zero

class AccountMoveLine(models.Model):
    """ Inherit Account Move Line """
    _inherit = 'account.move.line'

    @api.depends(
        'expense_move_id', 'expense_move_currency_id',
        'expense_move_id.manual_currency_rate_active',
        'expense_move_id.inverse_manual_currency_rate',
        'expense_move_id.invoice_date',
        'price_total', 'price_subtotal')
    def _compute_expense_price_move_currency_id(self):
        """ Compute Expense Move Currency ID """
        non_manual_rate = self
        for line in self:
            if not line.expense_move_id or \
                not line.expense_move_currency_id or \
                not line.expense_move_id.manual_currency_rate_active or \
                float_is_zero(
                    line.expense_move_id.inverse_manual_currency_rate,
                    precision_rounding=line.expense_move_currency_id.rounding):
                continue
            expense_move_currency_id = line.expense_move_currency_id or line.currency_id
            price_unit_expense_currency = line.price_unit
            total_expense_currency = line.price_total
            subtotal_expense_currency = line.price_subtotal
            if expense_move_currency_id != line.currency_id:
                manual_rate = line.expense_move_id.manual_currency_rate
                price_unit_expense_currency = expense_move_currency_id.round(
                    line.price_unit * manual_rate)
                total_expense_currency = expense_move_currency_id.round(
                    line.price_total * manual_rate)
                subtotal_expense_currency = expense_move_currency_id.round(
                    line.price_subtotal * manual_rate)
            line.update({
                'price_unit_expense_currency': price_unit_expense_currency,
                'total_expense_currency': total_expense_currency,
                'subtotal_expense_currency': subtotal_expense_currency,})
            non_manual_rate -= line
        if non_manual_rate:
            return super(AccountMoveLine, non_manual_rate)._compute_expense_price_move_currency_id()
