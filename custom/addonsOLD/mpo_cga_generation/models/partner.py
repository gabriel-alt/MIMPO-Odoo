""" Partner """
from odoo import fields, models

class ResPartner(models.Model):
    """ Inherit Res Partner """
    _inherit = 'res.partner'

    property_account_fondo_confiado_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Fondo Confiado",
        domain="[('trust_fund', '=', True)]")
    property_account_deposit_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Depósito en garantía",)

    def get_vals_account_partner_ref(self, company_ids):
        account_vals = super(
            ResPartner, self).get_vals_account_partner_ref(company_ids)
        for com in company_ids:
            if com.id not in account_vals:
                account_vals[com.id] = {}
            fondo_id = self.process_search_account(
                com_id=com.id, type='liability_current',
                code='217.01.'+ self.partner_ref + '.00')
            if not fondo_id:
                fondo_id = self.process_create_account(
                    com_id=com.id, type='liability_current',
                    code='217.01.'+ self.partner_ref + '.00')
                if fondo_id:
                    account_vals[com.id][
                        'property_account_fondo_confiado_id'] = fondo_id.id
            elif fondo_id and fondo_id != self.with_company(
                com).property_account_fondo_confiado_id.id:
                account_vals[com.id][
                    'property_account_fondo_confiado_id'] = fondo_id
            deposit_id = self.process_search_account(
                com_id=com.id, type='asset_current',
                code='184.03.'+ self.partner_ref + '.00')
            if not deposit_id:
                deposit_id = self.process_create_account(
                    com_id=com.id, type='asset_current',
                    code='184.03.'+ self.partner_ref + '.00')
                if deposit_id:
                    account_vals[com.id][
                        'property_account_deposit_id'] = deposit_id.id
            elif deposit_id and deposit_id != self.with_company(
                com).property_account_deposit_id.id:
                account_vals[com.id][
                    'property_account_deposit_id'] = deposit_id
        return account_vals
