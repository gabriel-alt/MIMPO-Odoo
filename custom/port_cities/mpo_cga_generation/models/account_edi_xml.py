""" Account EDI XML """
from odoo import models
from odoo.tools.float_utils import float_round


class AccountEdiXmlCii(models.AbstractModel):
    """ Inherit Account Edi Xml CII"""

    _inherit = "account.edi.xml.cii"

    def _export_invoice_vals(self, invoice):
        """ Inherit Export Invoice Vals """
        
        valid_lines = invoice.invoice_line_ids.filtered(
            lambda l: not l.include_from_xml
        )
        
        currency = invoice.currency_id
        subtotal = 0.0
        total_tax = 0.0
        conceptos = []

        for line in valid_lines:
            price_subtotal = line.price_subtotal
            subtotal += price_subtotal

            # Calcular impuestos manualmente
            taxes = line.tax_ids.compute_all(
                line.price_unit,
                currency,
                line.quantity,
                product=line.product_id,
                partner=invoice.partner_id,
            )

            conceptos.append(
                {
                    "cantidad": line.quantity,
                    "unidad": line.product_uom_id.name,
                    "descripcion": line.name,
                    "valor_unitario": line.price_unit,
                    "importe": price_subtotal,
                    "impuestos": taxes["taxes"],
                    "producto_id": line.product_id.default_code or "",
                    "clave_prod_serv": line.product_id.unspsc_code_id.code or "",
                }
            )

            for tax in taxes["taxes"]:
                total_tax += tax["amount"]

        subtotal = float_round(subtotal, precision_rounding=currency.rounding)
        total_tax = float_round(total_tax, precision_rounding=currency.rounding)
        total = subtotal + total_tax

        # Construir valores base (puedes extender según lo que necesites)
        values = {
            "subtotal": subtotal,
            "total": total,
            "moneda": currency.name,
            "conceptos": conceptos,
            "impuestos": total_tax,
        }

        return values
