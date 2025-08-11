""" Account Move """
import base64
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        #Extend function render qweb pdf for set invoice template to mimpo template
        if self._get_report(report_ref).report_name in (
            'account.report_invoice_with_payments', 'account.report_invoice'):
            invoices = self.env['account.move'].browse(res_ids)
            template, docids, label = invoices._get_mimpo_template_docids()
            if template:
                return super()._render_qweb_pdf(template, res_ids=docids, data=data)
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

class AccountJournal(models.Model):
    """ Inherit Account Journal """
    _inherit = 'account.journal'

    journal_type_print = fields.Selection([
        ('msa', 'Factura MSA'), ('cga', 'Factura CGA'),
        ('anticipo', 'Factura de anticipo')])

class AccountMove(models.Model):
    """ Inherit Account Move """

    _inherit = 'account.move'

    def compute_non_agency_expense(self):
        """ Compute Non Agency Expense """

        amount = 0.0
        for line in self.partner_expense_line_ids:
            amount += line.total_expense_currency
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

    def _get_mimpo_template_docids(self, show_error=False):
        msi = msdp = mscga = cga = msir = self.env['account.move']
        for move in self.filtered(lambda r: r.move_type in ['out_invoice', 'out_refund']):
            if move.journal_id.journal_type_print == 'msa':
                mscga |= move
            elif move.journal_id.journal_type_print == 'cga':
                cga |= move
            elif move.downpayment_invoice \
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
        if show_error:
            if (msi and (mscga or cga or msdp or msir)) or \
                (mscga and (msi or cga or msdp or msir)) or \
                (cga and (mscga or msi or msdp or msir)) or \
                (msdp and (mscga or msi or cga or msir)) or \
                (msir and (mscga or msi or cga or msdp)):
                raise ValidationError(_("Can't Print Multi Type Invoice Report at the Same Time!"))
            if not msi and not mscga and not cga and not msdp and not msir:
                raise ValidationError(_("No Invoice to Print!"))
        template, docids, label = '', [], ''
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
            template = self.env.ref(
                'mpo_cga_report.report_ms_cga_invoice', raise_if_not_found=False)
            # template = self.env.ref(
            #     'mpo_cga_report.report_cga_invoice', raise_if_not_found=False)
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
            docids = cga.ids
        return template, docids, label

    def action_print_invoice(self):
        """ Conditional Select Report Template """
        template, docids, label = self._get_mimpo_template_docids(show_error=True)
        if not template or not docids:
            raise ValidationError(_(f"Can't find {label} Invoice Report Template in the System"))
        report_action = template.report_action(docids, data=None)
        report_action.update({'close_on_report_download': True})
        return report_action

    def filter_ms_invoice_lines(self):
        """ Inherit Filter MS Invoice Lines """

        res = super(AccountMove, self).filter_ms_invoice_lines()
        # if self._context.get('ms_cga'):
        #     res = res.filtered(lambda r: not r.cga_line or (r.to_agency and r.cga_line))
        # else:
        #     res = res.filtered(lambda r: not r.cga_line and r.display_type == 'product')
        return res

    def get_cfdi_origin(self):
        """ Get CFDI Origin """
        if (self.down_payment_invoice_id or self.reversed_dp_inv_id) and \
            self.l10n_mx_edi_origin:
            split_origin = self.l10n_mx_edi_origin.split('|')
            res = ['07 - CFDI POR APLICACIÓN DE ANTICIPO', (
                split_origin and split_origin[1]) or '']
            return res
        return super(AccountMove, self).get_cfdi_origin()

    def _generate_mimpo_pdf_action(self):
        self.ensure_one()
        if self.move_type != 'out_invoice':
            return False
        template, docids, label = self._get_mimpo_template_docids()
        if template and docids:
            report = self.env['ir.actions.report']._render_qweb_pdf(
                template, docids)
            filename = self._get_report_base_filename() + '.pdf'
            if self.message_main_attachment_id:
                self.message_main_attachment_id.sudo().write({
                    'name': filename,
                    'datas': base64.b64encode(report[0]),
                })
            else:
                invoice_att = self.env['ir.attachment'].create({
                    'name': filename,
                    'type': 'binary',
                    'datas': base64.b64encode(report[0]),
                    'res_model': 'account.move',
                    'res_id': docids[0],
                    'mimetype': 'application/pdf'
                })
                self.write({'message_main_attachment_id': invoice_att.id})
        return True

    # Funcion que creaba la factura al guardar como borrador, se ha comentado porque no es necesario
    '''@api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        for move in res:
            move._generate_mimpo_pdf_action()
        return res'''

    def _post(self, soft=True):
        """ Inherit Post """
        posted = super()._post(soft=soft)
        for move in posted:
            move._generate_mimpo_pdf_action()
        return posted

    def button_cancel(self):
        """ Inherit Button Cancel """
        res = super(AccountMove, self).button_cancel()
        for move in self:
            move._generate_mimpo_pdf_action()
        return res

class AccountEdiDocument(models.Model):
    _inherit = 'account.edi.document'

    @api.model
    def _process_job(self, job):
        res = super(AccountEdiDocument, self)._process_job(job)
        documents = job['documents']
        if documents and documents.move_id:
            documents.move_id._generate_mimpo_pdf_action()
        return res
