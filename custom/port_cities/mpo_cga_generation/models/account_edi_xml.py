""" Account EDI XML """
from odoo import models


class AccountEdiXmlCii(models.AbstractModel):
    """ Inherit Account Edi Xml CII"""

    _inherit = "account.edi.xml.cii"

    def _export_invoice_vals(self, invoice):
        """ Inherit Export Invoice Vals """

        invoice = invoice.with_context(mx_edi=True)
        return super(AccountEdiXmlCii, self)._export_invoice_vals(invoice)
