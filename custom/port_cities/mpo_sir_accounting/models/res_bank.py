# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    def name_get(self):
        if self.env.context.get('default_move_type') in ['in_invoice', 'in_refund']:
            result = []
            for acc in self:
                name = acc.acc_number
                if acc.bank_id:
                    name = '{} - {}'.format(acc.acc_number, acc.bank_id.name)
                    if acc.bank_id.bic:
                        name += ' - ' + acc.bank_id.bic
                    if acc.bank_id.l10n_mx_edi_code:
                        name += ' - ' + acc.bank_id.l10n_mx_edi_code
                result.append((acc.id, name))
            return result
        return super(ResPartnerBank, self).name_get()
