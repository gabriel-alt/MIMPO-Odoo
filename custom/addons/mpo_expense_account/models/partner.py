""" Partner """
from odoo import fields, models


class ResPartner(models.Model):
    """ Inherit Res Partner """
    _inherit = 'res.partner'

    property_account_expense_partner_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Expense Account",
        domain="[('account_type', 'not in', ('asset_receivable','liability_payable','asset_cash','liability_credit_card')), ('deprecated', '=', False), ('company_id', '=', current_company_id), ('is_off_balance', '=', False)]",
        help="This account will be used instead of the default one as the expense account for the current partner")

    def get_vals_account_partner_ref(self, company_ids):
        account_vals = super(
            ResPartner, self).get_vals_account_partner_ref(company_ids)
        for com in company_ids:
            if com.id not in account_vals:
                account_vals[com.id] = {}
            exp_id = self.process_search_account(
                com_id=com.id, type='asset_current',
                code='106.01.'+ self.partner_ref + '.00')
            if not exp_id:
                exp_id = self.process_create_account(
                    com_id=com.id, type='asset_current',
                    code='106.01.'+ self.partner_ref + '.00')
                if exp_id:
                    account_vals[com.id][
                        'property_account_expense_partner_id'] = exp_id.id
            elif exp_id and exp_id != self.with_company(
                com).property_account_expense_partner_id.id:
                account_vals[com.id][
                    'property_account_expense_partner_id'] = exp_id
        return account_vals
