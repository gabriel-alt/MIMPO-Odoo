""" Account Move """
from odoo import models, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    """ Inherit Account Move """

    _inherit = 'account.move'

    def compute_non_agency_expense(self):
        """ Compute Non Agency Expense """

        amount = 0.0
        for line in self.partner_expense_line_ids:
            amount += line.total_expense
        return amount

    def _l10n_mx_amount_to_text_from_amount(self, amount):
        """Method to transform a float amount to text words
        E.g. 100 - ONE HUNDRED
        :returns: Amount transformed to words mexican format for invoices
        :rtype: str
        """
        self.ensure_one()

        currency_name = self.currency_id.name.upper()

        # M.N. = Moneda Nacional (National Currency)
        # M.E. = Moneda Extranjera (Foreign Currency)
        currency_type = 'M.N' if currency_name == 'MXN' else 'M.E.'

        # Split integer and decimal part
        amount_i, amount_d = divmod(amount, 1)
        amount_d = round(amount_d, 2)
        amount_d = int(round(amount_d * 100, 2))

        words = self.currency_id.with_context(lang=self.partner_id.lang or 'es_ES').amount_to_text(amount_i).upper()
        return '%(words)s %(amount_d)02d/100 %(currency_type)s' % {
            'words': words,
            'amount_d': amount_d,
            'currency_type': currency_type,
        }

    def action_print_invoice(self):
        """ Conditional Select Report Template """

        msi = msdp = mscga = cga = msir = self.env['account.move']
        for move in self.filtered(lambda r: r.move_type in ['out_invoice', 'out_refund']):
            if move.downpayment_invoice \
                    or (move.move_type == 'out_refund' \
                        and move.reversed_entry_id.downpayment_invoice):
                msdp |= move
            elif not move.partner_expense_line_ids and move.move_type == 'out_invoice':
                msi |= move
            elif not move.partner_expense_line_ids and move.move_type == 'out_refund':
                msir |= move
            elif move.partner_expense_line_ids \
                    and move.invoice_line_ids.filtered(
                        lambda r: r.display_type == 'product' \
                            and (not r.cga_line or (r.cga_line and r.product_id))):
                mscga |= move
            elif move.partner_expense_line_ids:
                cga |= move
        if (msi and (mscga or cga or msdp or msir)) or \
            (mscga and (msi or cga or msdp or msir)) or \
            (cga and (mscga or msi or msdp or msir)) or \
            (msdp and (mscga or msi or cga or msir)) or \
            (msir and (mscga or msi or cga or msdp)):
            raise ValidationError(_("Can't Print Multi Type Invoice Report at the Same Time!"))
        if not msi and not mscga and not cga and not msdp and not msir:
            raise ValidationError(_("No Invoice to Print!"))
        docids = []
        if msi:
            template = self.env.ref(
                'mpo_invoice_report.account_invoices_mpo_invoice_report', raise_if_not_found=False)
            label = "MS"
            docids = msi.ids
        elif msir:
            template = self.env.ref(
                'mpo_invoice_report.account_invoices_mpo_credit_note_report',
                raise_if_not_found=False)
            label = "MS Credit Note"
            docids = msir.ids
        elif mscga:
            # template = self.env.ref(
            #     'mpo_cga_report.report_ms_cga_invoice', raise_if_not_found=False)
            template = self.env.ref(
                'mpo_cga_report.report_cga_invoice', raise_if_not_found=False)
            label = "MS+CGA"
            docids = mscga.ids
        elif msdp:
            template = self.env.ref(
                'mpo_invoice_report.account_invoices_mpo_downpayment_invoice_report',
                raise_if_not_found=False)
            label = "MS Downpayment"
            docids = msdp.ids
        elif cga:
            template = self.env.ref(
                'mpo_cga_report.report_cga_invoice', raise_if_not_found=False)
            label = "CGA"
            docids = self.ids
        if not template or not docids:
            raise ValidationError(_(f"Can't find {label} Invoice Report Template in the System"))
        report_action = template.report_action(docids, data=None)
        report_action.update({'close_on_report_download': True})
        return report_action

    def filter_ms_invoice_lines(self):
        """ Inherit Filter MS Invoice Lines """

        res = super(AccountMove, self).filter_ms_invoice_lines()
        # Exclude CGA Lines
        # if self._context.get('ms_cga'):
        #     res = res.filtered(lambda r: not r.cga_line or (r.product_id and r.cga_line))
        res = res.filtered(lambda r: not r.cga_line)
        return res
