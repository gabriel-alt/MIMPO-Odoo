from odoo import fields, models, api,_


class ResPartner(models.Model):
    _inherit = 'res.partner'

    cortefiel_vendor = fields.Char()
    addenda_pedimento = fields.Boolean()

    @api.onchange('cortefiel_vendor')
    def _onchange_cortefiel_vendor(self):
        if self.cortefiel_vendor and self.l10n_mx_edi_addenda:
            self.l10n_mx_edi_addenda = False
