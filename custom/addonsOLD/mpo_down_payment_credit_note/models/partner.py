""" Partner """
from odoo import fields, models


class ResPartner(models.Model):
    """ Inherit Res Partner """
    _inherit = 'res.partner'

    property_account_down_payment_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Account Down Payment",
        domain="[('account_type', '=', 'liability_current'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
        help="This account will be used instead of the default one as the receivable account for the current partner")

    def get_vals_account_partner_ref(self, company_ids):
        account_vals = super(
            ResPartner, self).get_vals_account_partner_ref(company_ids)
        for com in company_ids:
            if com.id not in account_vals:
                account_vals[com.id] = {}
            dp_id = self.process_search_account(
                com_id=com.id, type='liability_current',
                code='206.01.'+ self.partner_ref + '.00')
            if not dp_id:
                dp_id = self.process_create_account(
                    com_id=com.id, type='liability_current',
                    code='206.01.'+ self.partner_ref + '.00')
                if dp_id:
                    account_vals[com.id][
                        'property_account_down_payment_id'] = dp_id.id
            elif dp_id and dp_id != self.with_company(
                com).property_account_down_payment_id.id:
                account_vals[com.id][
                    'property_account_down_payment_id'] = dp_id
        return account_vals
