'''product.template'''
from odoo import fields, models, _
from odoo.exceptions import UserError

ACCOUNT_DOMAIN = "['&', '&', '&', ('deprecated', '=', False), ('account_type', 'not in', \
    ('asset_receivable','liability_payable','asset_cash','liability_credit_card')), \
    ('company_id', '=', current_company_id), ('is_off_balance', '=', False)]"


class ProductTemplate(models.Model):
    '''inherit product.template'''

    _inherit = 'product.template'

    property_payment_third_party_account_id = fields.Many2one('account.account', 
        string='Pagos a cuenta de terceros', tracking=True, company_dependent=True,
        domain=ACCOUNT_DOMAIN)


class ProductProduct(models.Model):
    '''inherit product.product'''

    _inherit = 'product.product'

    def _check_account_third_party(self):
        '''check 3rd account product'''

        if not self.property_payment_third_party_account_id:
            raise UserError(_("Please set account of payment third party "
                "in the  product %s account configuration!",
                self.display_name))

