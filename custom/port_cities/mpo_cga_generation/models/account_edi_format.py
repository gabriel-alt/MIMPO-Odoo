"""Account EDI Format"""

from odoo import models, api, _


class AccountEdiFormat(models.Model):
    """Inherit Account EDI Format"""

    _inherit = "account.edi.format"

    @api.model
    def _l10n_mx_edi_check_configuration(self, move):
        """Replace l10n MX Edi Check Configuration"""

        company = move.company_id
        pac_name = company.l10n_mx_edi_pac

        errors = []

        # == Check the certificate ==
        certificate = (
            company.l10n_mx_edi_certificate_ids.sudo()._get_valid_certificate()
        )
        if not certificate:
            errors.append(_("No valid certificate found"))

        # == Check the credentials to call the PAC web-service ==
        if pac_name:
            pac_test_env = company.l10n_mx_edi_pac_test_env
            pac_password = company.sudo().l10n_mx_edi_pac_password
            if not pac_test_env and not pac_password:
                errors.append(_("No PAC credentials specified."))
        else:
            errors.append(_("No PAC specified."))

        # == Check the 'l10n_mx_edi_decimal_places' field set on the currency  ==
        currency_precision = move.currency_id.l10n_mx_edi_decimal_places
        if currency_precision is False:
            errors.append(
                _(
                    "The SAT does not provide information for the currency %s.\n"
                    "You must get manually a key from the PAC to confirm the "
                    "currency rate is accurate enough."
                )
                % move.currency_id
            )

        # == Check the invoice ==
        if move.l10n_mx_edi_cfdi_request in ("on_invoice", "on_refund"):
            # CUSTOM: exclude CGA lines from validation
            negative_lines = move.invoice_line_ids.filtered(
                lambda line: not line.cga_line and line.price_subtotal < 0
            )
            if negative_lines:
                # Line having a negative amount is not allowed.
                if not move._l10n_mx_edi_is_managing_invoice_negative_lines_allowed():
                    errors.append(
                        _(
                            "Invoice lines having a negative amount are not allowed to generate the CFDI. "
                            "Please create a credit note instead."
                        )
                    )
                # Discount line without taxes is not allowed.
                if negative_lines.filtered(lambda line: not line.tax_ids):
                    errors.append(
                        _(
                            "Invoice lines having a negative amount without a tax set is not allowed to "
                            "generate the CFDI."
                        )
                    )
            invalid_unspcs_products = move.invoice_line_ids.product_id.filtered(
                lambda product: not product.unspsc_code_id
            )
            if invalid_unspcs_products:
                errors.append(
                    _(
                        "You need to define an 'UNSPSC Product Category' on the following products: %s"
                    )
                    % ", ".join(invalid_unspcs_products.mapped("display_name"))
                )
        return errors

    def _l10n_mx_edi_get_invoice_cfdi_values(self, invoice):
        """Inherit l10n MX EDI Get Invoice CFDI Values"""

        # add context MX EDI into invoice
        invoice = invoice.with_context(mx_edi=True)
        res = super(AccountEdiFormat, self)._l10n_mx_edi_get_invoice_cfdi_values(
            invoice
        )

        valid_lines = invoice.invoice_line_ids.filtered(
            lambda l: not l.exclude_from_xml and not l.cga_line
        )
        currency = invoice.currency_id
        subtotal = 0.0
        tax_transferred = 0.0
        tax_withholding = 0.0

        for line in valid_lines:
            subtotal += line.price_subtotal

            tax_data = line.tax_ids.compute_all(
                line.price_unit,
                currency,
                line.quantity,
                product=line.product_id,
                partner=invoice.partner_id,
            )

            for tax in tax_data["taxes"]:
                if tax["type"] == "withholding":
                    tax_withholding += tax["amount"]
                else:
                    tax_transferred += tax["amount"]

        total = subtotal + tax_transferred - tax_withholding

        # Reemplazar los valores en el diccionario resultante
        res.update(
            {
                "total_price_subtotal_before_discount": subtotal,
                "amount_total": total,
                "tax_details_transferred": {"tax_amount": tax_transferred},
                "tax_details_withholding": {"tax_amount": tax_withholding},
                "total_price_non_cga": total,  # si quieres seguir usando esta key
            }
        )

        return res
