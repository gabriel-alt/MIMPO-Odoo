""" Account Move """
from odoo import models
from odoo.tools import float_compare
from odoo.tools.misc import formatLang


class AccountMove(models.Model):
    """ Inherit Account Move """

    _inherit = 'account.move'

    def _get_pedimento_date(self):
        self.ensure_one()
        if not self.sir_id.date_ph:
            return ' '
        date_ph = self.sir_id.date_ph
        for dph in date_ph.split():
            if len(dph) == 10:
                return dph
        return date_ph

    def _get_complete_pedimento(self):
        pedimento = self.pedimento or ''
        try:
            if self.sir_id.patent_code:
                pedimento = self.sir_id.patent_code + '-' + pedimento
            have_house = False
            if self.house_id and self.house_id.number:
                pedimento = self.house_id.number + '-' + pedimento
                have_house = True
            elif self.custom_house:
                pedimento = self.custom_house[:2] + '-' + pedimento
                have_house = True
            date_ph = self._get_pedimento_date()
            if date_ph:
                if not have_house:
                    pedimento = '-' + pedimento
                if len(date_ph) == 10:
                    pedimento = date_ph[-2:] + pedimento
                else:
                    pedimento = self.sir_id.date_ph[8:10] + pedimento
        except:
            pedimento = self.pedimento
        return pedimento

    def _get_format_price(self, amount=0.0, digits=2, currency_id=False):
        self.ensure_one()
        if not currency_id:
            currency_id = self.currency_id
        return formatLang(self.env, amount, digits=digits, currency_obj=currency_id)

    def _get_total_tax16_base(self, tax_totals={}):
        self.ensure_one()
        tax16 = 0.0
        ms_lines = self.filter_ms_invoice_lines()
        if not ms_lines:
            tax_totals = self.tax_totals
        if tax_totals.get('subtotals'):
            for subtotal in tax_totals['subtotals']:
                for tax in tax_totals['groups_by_subtotal'][subtotal['name']]:
                    if '16' in tax.get('tax_group_name'):
                        tax16 += tax.get('tax_group_amount')
        return tax16

    def _get_gastos_efectuados_line(self):
        self.ensure_one()
        lines = self.env['account.move.line']
        for line in self.invoice_line_ids:
            if line.trust_fund_account_id or not line.cga_line or \
                not line.origin_expense_line_ids:
                continue
            if line.origin_expense_line_id and \
                not line.origin_expense_line_id.move_id.to_agency:
                lines |= line
            elif all(not l.move_id.to_agency for l in line.origin_expense_line_ids):
                lines |= line
        return lines

    def filter_ms_invoice_lines(self):
        """ FIlter MS Invoice Lines to Print """
        # Exclude CGA Lines
        res = self.invoice_line_ids.sorted(
            key=lambda l: (-l.sequence, l.date, l.move_name, -l.id), reverse=True)
        gastos_line = self._get_gastos_efectuados_line()
        if gastos_line:
            return res.filtered(lambda r: not r.cga_line or r.id not in gastos_line.ids)
        return res

    def get_ms_invoice_lines(self):
        """ Parse Invoice Lines to Print """

        lines = []
        ms_lines = self.filter_ms_invoice_lines()
        for line in ms_lines:
            vals = {'display_type': line.display_type, 'name': line.name,
                    'price_subtotal': 0.0, 'price_total': 0.0}
            if line.display_type == 'product' and not line.product_id:
                continue
            if line.display_type == 'product' and line.product_id:
                #checking taxes
                flag = -1 if self.move_type == 'out_refund' else 1
                line_discount_price_unit = flag * line.price_unit * (
                    1 - (line.discount / 100.0))
                taxes_res = line.tax_ids.compute_all(
                    line_discount_price_unit,
                    quantity=line.quantity,
                    currency=line.currency_id,
                    product=line.product_id,
                    partner=line.partner_id,
                    is_refund=line.is_refund,
                )
                dict_tax = {}
                list_tax = []
                for tax in taxes_res.get('taxes'):
                    tax_id = line.tax_ids.filtered(lambda t: t.id == tax.get('id'))
                    if not tax_id:
                        continue
                    if tax_id.impuesto_tax_code and tax_id.impuesto_tax_name:
                        tax_name = tax_id.impuesto_tax_code + ' - ' + \
                            tax_id.impuesto_tax_name
                    elif tax_id.impuesto_tax_code:
                        tax_name = tax_id.impuesto_tax_code
                    elif tax_id.impuesto_tax_name:
                        tax_name = tax_id.impuesto_tax_name
                    else:
                        tax_name = tax_id.description or tax_id.name
                    if tax.get('id') not in dict_tax:
                        dict_tax[tax.get('id')] = {'name': tax_name, 'amount': 0}
                    dict_tax[tax.get('id')]['amount'] += tax.get('amount')
                    txt_amount = formatLang(
                        self.env, dict_tax[tax.get('id')]['amount'],
                        digits=2, currency_obj=line.currency_id)
                    if txt_amount and tax_name:
                        txt_amount = str(tax_name) + ' ' + str(txt_amount)
                    list_tax.append(txt_amount)
                #end check taxes
                check = [x for x in lines if lines and x.get(
                    'product_id') == line.product_id]
                if check:
                    init_price = check[0].get('price_unit', 0.0) \
                        if float_compare(check[0].get('quantity', 0.0), 1.0,
                                         precision_rounding=check[0].get(
                                             'product_uom_id').rounding) <= 0 \
                        else check[0].get(
                            'price_unit', 0.0) * check[0].get('quantity', 0.0)
                    #check for same taxes
                    next_dtax = {}
                    next_ltax = []
                    for ct_id, ct_dict in check[0].get('dict_tax').items():
                        next_dtax[ct_id] = ct_dict
                        if ct_id in dict_tax:
                            next_dtax[ct_id]['amount'] += dict_tax[ct_id].get('amount')
                        txt_amount = formatLang(
                            self.env, next_dtax[ct_id]['amount'],
                            currency_obj=line.currency_id)
                        if txt_amount and next_dtax[ct_id]['name']:
                            txt_amount = str(next_dtax[ct_id][
                                'name']) + ' ' + str(txt_amount)
                        next_ltax.append(txt_amount)
                    check[0].update({
                        'price_subtotal': check[0].get('price_subtotal', 0.0) \
                            + (flag * (line.price_subtotal or 0.0)),
                        'price_total': check[0].get('price_total', 0.0) \
                            + (flag * (line.price_total or 0.0)),
                        'price_unit': init_price \
                            + (flag * (line.price_unit * line.quantity)),
                        'quantity': 1.0,
                        'dict_tax': next_dtax,
                        'list_tax': next_ltax})
                    continue
                vals.update({'product_id': line.product_id,
                            'product_code': line.product_id.default_code,
                            'product_name': line.product_id.name,
                            'product_unspsc_code': line.product_id.unspsc_code_id.code or ' ',
                            'product_uom_id': line.product_uom_id,
                            'uom_unspsc_code': line.product_uom_id.unspsc_code_id.code or ' ',
                            'uom_unspsc_name': line.product_uom_id.unspsc_code_id.name or ' ',
                            'quantity': line.quantity,
                            'price_unit': flag * line.price_unit,
                            'price_subtotal': flag * (line.price_subtotal or 0.0),
                            'price_total': flag * (line.price_total or 0.0),
                            'tax_ids': line.tax_ids,
                            'dict_tax': dict_tax,
                            'list_tax': list_tax})
            lines.append(vals)
        return lines

    def _get_tax_totals_mimpo(self):
        self.ensure_one()
        ms_lines = self.filter_ms_invoice_lines()
        if not ms_lines:
            return {
                'amount_untaxed': 0.0,
                'amount_total': 0.0,
                'formatted_amount_total': formatLang(self.env, 0.0, currency_obj=self.currency_id),
                'formatted_amount_untaxed': formatLang(self.env, 0.0, currency_obj=self.currency_id),
                'groups_by_subtotal': {},
                'subtotals': {},
                'subtotals_order': {},
                'display_tax_base': False}
        base_lines = ms_lines.filtered(
            lambda line: line.display_type == 'product')
        base_line_values_list = [line._convert_to_tax_base_line_dict() for line in base_lines]
        sign = self.direction_sign
        if self.id:
            # The invoice is stored so we can add the early payment discount lines directly to reduce the
            # tax amount without touching the untaxed amount.
            base_line_values_list += [
                {
                    **line._convert_to_tax_base_line_dict(),
                    'handle_price_include': False,
                    'quantity': 1.0,
                    'price_unit': sign * line.amount_currency,
                }
                for line in self.line_ids.filtered(lambda line: line.display_type == 'epd')
            ]

        kwargs = {
            'base_lines': base_line_values_list,
            'currency': self.currency_id or self.journal_id.currency_id or self.company_id.currency_id,
        }

        if self.id:
            kwargs['tax_lines'] = [
                line._convert_to_tax_line_dict()
                for line in self.line_ids.filtered(lambda line: line.display_type == 'tax')
            ]
        else:
            # In case the invoice isn't yet stored, the early payment discount lines are not there. Then,
            # we need to simulate them.
            epd_aggregated_values = {}
            for base_line in base_lines:
                if not base_line.epd_needed:
                    continue
                for grouping_dict, values in base_line.epd_needed.items():
                    epd_values = epd_aggregated_values.setdefault(grouping_dict, {'price_subtotal': 0.0})
                    epd_values['price_subtotal'] += values['price_subtotal']

            for grouping_dict, values in epd_aggregated_values.items():
                taxes = None
                if grouping_dict.get('tax_ids'):
                    taxes = self.env['account.tax'].browse(grouping_dict['tax_ids'][0][2])

                kwargs['base_lines'].append(self.env['account.tax']._convert_to_tax_base_line_dict(
                    None,
                    partner=self.partner_id,
                    currency=self.currency_id,
                    taxes=taxes,
                    price_unit=values['price_subtotal'],
                    quantity=1.0,
                    account=self.env['account.account'].browse(grouping_dict['account_id']),
                    analytic_distribution=values.get('analytic_distribution'),
                    price_subtotal=values['price_subtotal'],
                    is_refund=self.move_type in ('out_refund', 'in_refund'),
                    handle_price_include=False,
                    extra_context={'_extra_grouping_key_': 'epd'},
                ))
        return self.env['account.tax']._prepare_tax_totals(**kwargs)

    def _l10n_mx_edi_mimpo_amount_to_text(self, amount=0.0):
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

        words = self.currency_id.with_context(
            lang=self.partner_id.lang or 'es_ES').amount_to_text(
                amount_i).upper()
        return '%(words)s %(amount_d)02d/100 %(currency_type)s' % {
            'words': words,
            'amount_d': amount_d,
            'currency_type': currency_type,
        }

    def get_cfdi_origin(self):
        """ Get CFDI Origin """

        res = []
        if self.l10n_mx_edi_origin:
            code = [('01', '01 - NOTA DE CRÉDITO'),
                    ('02', '02 - NOTA DE DÉBITO DE LOS DOCUMENTOS RELACIONADOS'),
                    ('03', '03 - DEVOLUCIÓN DE MERCANCÍA SOBRE FACTURAS O TRASLADOS PREVIOS'),
                    ('04', '04- SUSTITUCIÓN DE LOS CFDI PREVIOS'),
                    ('05', '05 - TRASLADOS DE MERCANCÍAS FACTURADOS PREVIAMENTE'),
                    ('06', '06 - FACTURA GENERADA POR LOS TRASLADOS PREVIOS'),
                    ('07', '07 - CFDI POR APLICACIÓN DE ANTICIPO')]
            split_origin = self.l10n_mx_edi_origin.split('|')
            check = [x[1] for x in code if x[0] == split_origin[0]]
            res = [check[0] if check else '', (split_origin and split_origin[1]) or '']
        return res

    def get_related_downpayment(self):
        """ Get Related Downpayment """

        res = {}
        if self.l10n_mx_edi_origin:
            origin = self.l10n_mx_edi_origin.split('|')
            if len(origin) != 2:
                return res
            domain = [('l10n_mx_edi_cfdi_uuid', '=', origin[1])]
            downpayment = self.search_read(domain=domain, fields=['amount_total', 'invoice_date'], limit=1)
            if not downpayment:
                return res
            res.update(
                {'invoice_date': downpayment[0].get('invoice_date').strftime('%d/%m/%Y'),
                 'amount': downpayment[0].get('amount_total')})
        return res
