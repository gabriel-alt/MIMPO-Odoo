from odoo import api, models, fields, _
from odoo.exceptions import UserError

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    # def _convert(self, from_amount, to_currency, company, date, round=True):
    #     if not self.env.context.get('from_bill_line') and \
    #         not self.env.context.get('to_expense_move'):
    #         return super()._convert(from_amount, to_currency, company, date, round)

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        if self.env.context.get('from_bill_line') and \
            self.env.context.get('to_expense_move'):
            bill_line = self.env.context.get('from_bill_line')
            expense_move = self.env.context.get('to_expense_move')
            if from_currency != company.currency_id and \
                bill_line.move_id.manual_currency_rate_active and \
                    bill_line.move_id.inverse_manual_currency_rate:
                return bill_line.move_id.inverse_manual_currency_rate
            if to_currency != company.currency_id and \
                expense_move.manual_currency_rate_active and \
                    expense_move.manual_currency_rate:
                return expense_move.manual_currency_rate
        return super()._get_conversion_rate(from_currency, to_currency, company, date)
