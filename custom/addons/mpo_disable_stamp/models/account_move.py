# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_inv_process_now(self):
        edi_document_vals_list = []
        for move in self:
            for edi_format in move.journal_id.edi_format_ids:
                move_applicability = edi_format.with_context(
                    inv_process_now=True)._get_move_applicability(move)

                if move_applicability:
                    errors = edi_format._check_move_configuration(move)
                    if errors:
                        raise UserError(_(
                            "Invalid invoice configuration:\n\n%s"
                            ) % '\n'.join(errors))

                    existing_edi_document = move.edi_document_ids.filtered(
                        lambda x: x.edi_format_id == edi_format)
                    if existing_edi_document:
                        existing_edi_document.sudo().write({
                            'state': 'to_send',
                            'attachment_id': False,
                        })
                    else:
                        edi_document_vals_list.append({
                            'edi_format_id': edi_format.id,
                            'move_id': move.id,
                            'state': 'to_send',
                        })

        self.env['account.edi.document'].create(edi_document_vals_list)
        self.edi_document_ids._process_documents_no_web_services()
        self.env.ref('account_edi.ir_cron_edi_network')._trigger()
        return True

    def _post(self, soft=True):
        return super(AccountMove, self.with_context(
            move_post_stamp=True))._post(soft=soft)

class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _get_move_applicability(self, move):
        # EXTENDS account_edi
        self.ensure_one()
        if self.code == 'cfdi_3_3' and not self.env.context.get(
            'inv_process_now') and self.env.context.get('move_post_stamp'):
            return {}
        elif self.code != 'cfdi_3_3':
            return super(AccountEdiFormat, self)._get_move_applicability(move)
        if move.country_code != 'MX':
            return None

        if move.move_type in ('out_invoice', 'out_refund') and \
            move.company_id.currency_id.name == 'MXN':
            return {
                'post': self._l10n_mx_edi_post_invoice,
                'cancel': self._l10n_mx_edi_cancel_invoice,
                'edi_content': self._l10n_mx_edi_xml_invoice_content,
            }

        if (move.payment_id or move.statement_line_id
            ).l10n_mx_edi_force_generate_cfdi or \
                'PPD' in move._get_reconciled_invoices().mapped(
                    'l10n_mx_edi_payment_policy'):
            return {
                'post': self._l10n_mx_edi_post_payment,
                'cancel': self._l10n_mx_edi_cancel_payment,
                'edi_content': self._l10n_mx_edi_xml_payment_content,
            }
