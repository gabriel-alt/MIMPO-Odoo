""" Account Move """
from odoo import api, fields, models, _

class AccountMove(models.Model):
    """ Inherit Account Move """
    _inherit = 'account.move'

    down_payment_invoice_id = fields.Many2one(
        'account.move', string='Down Payment Invoice',
        copy=False, tracking=True,
        domain="[('related_dp_invoice_ids', '=', False), ('downpayment_invoice', '=', True), ('partner_id', '=', partner_id), ('company_id', '=', company_id), ('sir_id', '=', sir_id)]")
    related_dp_invoice_ids = fields.One2many(
        'account.move', 'down_payment_invoice_id', readonly=True)
    show_related_dp_invoice = fields.Boolean(
        compute='_compute_show_related_dp_invoice')
    reversed_dp_inv_id = fields.Many2one(
        comodel_name='account.move', string="Reversal Down Payment",
        readonly=True, copy=False, check_company=True,)
    reversal_dp_inv_ids = fields.One2many('account.move', 'reversed_dp_inv_id')

    def _get_related_dp_invoice(self):
        self.ensure_one()
        invoice_list = []
        if self.down_payment_invoice_id and \
            self.down_payment_invoice_id.reversal_dp_inv_ids:
            invoice_list.append(self.down_payment_invoice_id.id)
            for rm in self.down_payment_invoice_id.reversal_dp_inv_ids:
                invoice_list.append(rm.id)
        elif self.downpayment_invoice and self.related_dp_invoice_ids and \
            self.reversal_dp_inv_ids:
            for rdi in self.related_dp_invoice_ids:
                invoice_list.append(rdi.id)
            for rm in self.reversal_dp_inv_ids:
                invoice_list.append(rm.id)
        elif self.reversed_dp_inv_id and \
            self.reversed_dp_inv_id.related_dp_invoice_ids:
            invoice_list.append(self.reversed_dp_inv_id.id)
            for rdi in self.reversed_dp_inv_id.related_dp_invoice_ids:
                invoice_list.append(rdi.id)
        return invoice_list

    def _compute_show_related_dp_invoice(self):
        for this in self:
            if this._get_related_dp_invoice():
                this.show_related_dp_invoice = True
            else:
                this.show_related_dp_invoice = False

    def open_related_dp_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Related Invoices"),
            'res_model': 'account.move',
            'view_mode': 'form',
            'domain': [('id', 'in', self._get_related_dp_invoice())],
            'views': [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form')],
            'context': {'create': 0, 'delete': 0,},
        }

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        super(AccountMove, self)._onchange_journal_id()
        if self.journal_id and self.journal_id.down_payment_journal and \
            not self.downpayment_invoice:
            self.downpayment_invoice = self.journal_id.down_payment_journal

    @api.onchange('sir_id')
    def _onchange_sir(self):
        super(AccountMove, self)._onchange_sir()
        for move in self:
            if move.sir_id.move_ids:
                dp_inv = move.sir_id.move_ids.filtered(
                    lambda m: m.downpayment_invoice and \
                    m.move_type == 'out_invoice' and m.state == 'posted' and \
                    not m.related_dp_invoice_ids)
                if dp_inv:
                    move.down_payment_invoice_id = dp_inv[0].id

    @api.onchange('downpayment_invoice')
    def _onchange_downpayment_invoice(self):
        for move in self:
            if move.downpayment_invoice and move.down_payment_invoice_id:
                move.down_payment_invoice_id = False

    @api.onchange('down_payment_invoice_id')
    def _onchange_down_payment_invoice_id(self):
        """onchange for set cfdi"""
        if self.down_payment_invoice_id and \
            self.down_payment_invoice_id.l10n_mx_edi_cfdi_uuid:
            cfdi = '07|' + self.down_payment_invoice_id.l10n_mx_edi_cfdi_uuid
            self.l10n_mx_edi_origin = cfdi
        elif self.l10n_mx_edi_origin:
            self.l10n_mx_edi_origin = ''

    @api.model
    def _l10n_mx_edi_write_cfdi_origin(self, code, uuids):
        if self.env.context.get('from_cn_dp'):
            return self.env.context.get('from_cn_dp')
        return super(AccountMove, self)._l10n_mx_edi_write_cfdi_origin(
            code, uuids)

    def generate_cn_down_payment_invoice(self):
        self.ensure_one()
        dp_inv_id = self.down_payment_invoice_id
        vals = {
            'date': fields.Date.context_today(self),
            'invoice_date_due': fields.Date.context_today(self),
            'invoice_date': fields.Date.context_today(self)
        }
        new_edi_origin = ''
        if self.l10n_mx_edi_cfdi_uuid:
            new_edi_origin = '07|' + self.l10n_mx_edi_cfdi_uuid
        default_values_list = [vals]
        refund_id = dp_inv_id.with_context(
            from_cn_dp=new_edi_origin)._reverse_moves(
            default_values_list, cancel=False)
        refund_vals = {
            'reversed_entry_id': False,
            'reversed_dp_inv_id': refund_id.reversed_entry_id.id or False,}
        if self.l10n_mx_edi_cfdi_uuid:
            refund_vals['l10n_mx_edi_origin'] = '07|' + self.l10n_mx_edi_cfdi_uuid
        refund_id.write(refund_vals)
        refund_id._post(soft=False)
        return refund_id

    def _post(self, soft=True):
        """ Inherit Post """
        res = super(AccountMove, self)._post(soft=soft)
        for move in res.filtered(
            lambda r: r.move_type == 'out_invoice' and r.down_payment_invoice_id):
            move.generate_cn_down_payment_invoice()
        return res

    def write(self, vals):
        """extend write"""
        res = super(AccountMove, self).write(vals)
        if vals.get('edi_document_ids') or vals.get('l10n_mx_edi_cfdi_uuid'):
            for this in self:
                if this.l10n_mx_edi_cfdi_uuid and \
                    this.down_payment_invoice_id and \
                    this.down_payment_invoice_id.reversal_move_id:
                    new_cfdi = '07|' + this.l10n_mx_edi_cfdi_uuid
                    this.down_payment_invoice_id.reversal_move_id.write({
                        'l10n_mx_edi_origin': new_cfdi})
        return res

class AccountMoveLine(models.Model):
    """ Inherit Account Move Line"""
    _inherit = 'account.move.line'

    def _compute_account_id(self):
        super(AccountMoveLine, self)._compute_account_id()
        product_lines = self.filtered(
            lambda l: l.display_type == 'product' and \
            l.move_id.is_invoice(True) and l.move_id.downpayment_invoice and \
            l.move_id.move_type in ['out_invoice', 'out_refund'])
        for line in product_lines:
            if line.move_id.partner_id and line.move_id.company_id:
                partner_id = line.move_id.with_company(
                    line.move_id.company_id).partner_id
                if partner_id.property_account_down_payment_id:
                    line.account_id = partner_id.property_account_down_payment_id
                elif line.move_id.journal_id.default_account_id:
                    line.account_id = line.move_id.journal_id.default_account_id

class AccountEdiDocument(models.Model):
    _inherit = 'account.edi.document'

    def write(self, vals):
        """extend write"""
        res = super(AccountEdiDocument, self).write(vals)
        if vals.get('state') == 'sent':
            for this in self.mapped('move_id'):
                if this.l10n_mx_edi_cfdi_uuid and \
                    this.down_payment_invoice_id and \
                    this.down_payment_invoice_id.reversal_move_id:
                    new_cfdi = '07|' + this.l10n_mx_edi_cfdi_uuid
                    this.down_payment_invoice_id.reversal_move_id.write({
                        'l10n_mx_edi_origin': new_cfdi})
        return res
