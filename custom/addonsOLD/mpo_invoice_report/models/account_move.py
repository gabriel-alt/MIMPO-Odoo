""" Account Move """
from odoo import models
from odoo.tools import float_compare
from odoo.tools.misc import formatLang


class AccountMove(models.Model):
    """ Inherit Account Move """

    _inherit = 'account.move'

    def filter_ms_invoice_lines(self):
        """ FIlter MS Invoice Lines to Print """

        return self.invoice_line_ids.sorted(
            key=lambda l: (-l.sequence, l.date, l.move_name, -l.id), reverse=True)

    def get_ms_invoice_lines(self):
        """ Parse Invoice Lines to Print """

        lines = []
        ms_lines = self.filter_ms_invoice_lines()
        for line in ms_lines:
            vals = {'display_type': line.display_type,
                    'name': line.name}
            if line.display_type == 'product' and line.product_id:
                #checking taxes
                line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
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
                        currency_obj=line.currency_id)
                    if txt_amount and tax_name:
                        txt_amount = str(tax_name) + ' ' + str(txt_amount)
                    list_tax.append(txt_amount)
                #end check taxes
                check = [x for x in lines if lines and x.get('product_id') == line.product_id]
                if check:
                    init_price = check[0].get('price_unit', 0.0) \
                        if float_compare(check[0].get('quantity', 0.0), 1.0,
                                            precision_rounding=check[0].get('product_uom_id').rounding) <= 0 \
                        else check[0].get('price_unit', 0.0) * check[0].get('quantity', 0.0)
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
                            txt_amount = str(next_dtax[ct_id]['name']) + ' ' + str(txt_amount)
                        next_ltax.append(txt_amount)
                    check[0].update({'price_subtotal': check[0].get('price_subtotal', 0.0) \
                                        + line.price_subtotal,
                                        'price_total': check[0].get('price_total', 0.0) \
                                        + line.price_total,
                                        'price_unit': init_price \
                                        + (line.price_unit * line.quantity),
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
                            'price_unit': line.price_unit,
                            'price_subtotal': line.price_subtotal,
                            'price_total': line.price_total,
                            'tax_ids': line.tax_ids,
                            'dict_tax': dict_tax,
                            'list_tax': list_tax})
            lines.append(vals)
        return lines

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
