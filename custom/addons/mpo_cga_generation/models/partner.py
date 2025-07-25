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
    l10n_mx_edi_payment_policy = fields.Selection(
        string='Payment Policy',
        selection=[('PPD', 'PPD'), ('PUE', 'PUE')])
    l10n_mx_edi_usage = fields.Selection(
        selection=[
            ('G01', 'Acquisition of merchandise'),
            ('G02', 'Returns, discounts or bonuses'),
            ('G03', 'General expenses'),
            ('I01', 'Constructions'),
            ('I02', 'Office furniture and equipment investment'),
            ('I03', 'Transportation equipment'),
            ('I04', 'Computer equipment and accessories'),
            ('I05', 'Dices, dies, molds, matrices and tooling'),
            ('I06', 'Telephone communications'),
            ('I07', 'Satellite communications'),
            ('I08', 'Other machinery and equipment'),
            ('D01', 'Medical, dental and hospital expenses.'),
            ('D02', 'Medical expenses for disability'),
            ('D03', 'Funeral expenses'),
            ('D04', 'Donations'),
            ('D05', 'Real interest effectively paid for mortgage loans (room house)'),
            ('D06', 'Voluntary contributions to SAR'),
            ('D07', 'Medical insurance premiums'),
            ('D08', 'Mandatory School Transportation Expenses'),
            ('D09', 'Deposits in savings accounts, premiums based on pension plans.'),
            ('D10', 'Payments for educational services (Colegiatura)'),
            ('P01', 'To define (CFDI 3.3 only)'),
            ('S01', "Without fiscal effects"),
        ],
        string="Usage",
        help="Used in CFDI 3.3 to express the key to the usage that will gives the receiver to this invoice. This "
             "value is defined by the customer.\nNote: It is not cause for cancellation if the key set is not the usage "
             "that will give the receiver of the document.")

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
