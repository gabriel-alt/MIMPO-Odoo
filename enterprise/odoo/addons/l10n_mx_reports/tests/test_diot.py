# -*- coding: utf-8 -*-
# pylint: disable=bad-whitespace
from odoo import fields, Command
from odoo.tests import tagged

from odoo.addons.account_reports.tests.common import TestAccountReportsCommon


@tagged('post_install', 'post_install_l10n', '-at_install', 'l10n_mx_diot')
class TestDiot(TestAccountReportsCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref='l10n_mx.mx_coa'):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.purchase_taxes = cls._get_purchase_taxes()

        cls.partner_a.write({'country_id': cls.env.ref('base.mx').id, 'l10n_mx_type_of_operation': '85', 'vat': 'OTE2003102G1'})
        cls.partner_b.write({'country_id': cls.env.ref('base.us').id, 'l10n_mx_type_of_operation': '85', 'vat': '12-3456789'})

    @classmethod
    def _get_purchase_taxes(cls):
        taxes = cls.env['account.tax']
        for i in [1, 2, 7, 8, 13, 14, 16, 18, 19, 20, 21]:
            taxes += cls.env.ref(f'l10n_mx.{cls.env.company.id}_tax{i}')
        return taxes

    def test_diot_report(self):
        date_invoice = '2022-07-01'
        moves_vals = []
        for i, tax in enumerate(self.purchase_taxes):
            for partner in (self.partner_a, self.partner_b):
                moves_vals += [
                    {
                        'move_type': 'in_invoice',
                        'partner_id': partner.id,
                        'invoice_payment_term_id': False,
                        'invoice_date': date_invoice,
                        'date': date_invoice,
                        'invoice_line_ids': [Command.create({
                            'name': f'test {tax.amount}',
                            'quantity': 1,
                            'price_unit': 10 + 1 * i,
                            'tax_ids': [Command.set(tax.ids)],
                        })],
                    },
                    {
                        'move_type': 'in_refund',
                        'partner_id': partner.id,
                        'invoice_payment_term_id': False,
                        'invoice_date': date_invoice,
                        'date': date_invoice,
                        'invoice_line_ids': [Command.create({
                            'name': f'test {tax.amount}',
                            'quantity': 1,
                            'price_unit': 10 + 2 * i,
                            'tax_ids': [Command.set(tax.ids)],
                        })],
                    },
                ]

        moves = self.env['account.move'].create(moves_vals)
        moves.action_post()

        for move in moves:
            self.env['account.payment.register'].with_context(active_model='account.move', active_ids=move.ids).create({
                'payment_date': date_invoice,
                'journal_id': self.company_data['default_journal_bank'].id,
                'amount': move.amount_total,
            })._create_payments()

        self.assertTrue(all(m.payment_state in ('paid', 'in_payment') for m in moves))

        diot_report = self.env.ref('l10n_mx_reports.diot_report')

        options = self._generate_options(diot_report, fields.Date.from_string('2022-01-01'), fields.Date.from_string('2022-12-31'))
        options['unfold_all'] = True

        self.maxDiff = None
        self.assertLinesValues(
            diot_report._get_lines(options),
            # 1-4: partner info
            # 5-6: 8% N./refund, 7-8: 8% N./refund, 9-10: 16%/refund, 11-12: 16% imp/refund, 13-14: 16% int_imp/refund
            # 15-19: creditable in same order, 20-24: non-creditable in same order
            # 25: withheld, 26: exempt, 27: exempt imports, 28: 0%, 29: no tax object
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
            [
                ('', '', '', '', 32.00, 3.52, 40.00, 4.80, 64.00, 14.08, 36.00, 8.32, 38.00, 8.96, 32.00, 40.00, 30.00, 36.00, 38.00, '', '', 34.00, '', '', -1.26, '', '', 28.00, ''),

                ('04', '85', 'OTE2003102G1', 'MEX', 16.00, 1.76, 20.00, 2.40, 32.00, 7.04, 18.00, 4.16, 19.00, 4.48, 16.00, 20.00, 15.00, 18.00, 19.00, '', '', 17.00, '', '', -0.63, '', '', 14.00, ''),
                ('', '', '', '', '', '', '', 2.40, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', 20.00, '', '', '', '', '', '', '', '', 20.00, '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', 4.48, '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', 19.00, '', '', '', '', '', 19.00, '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', 4.16, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', 18.00, '', '', '', '', '', '', 18.00, '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', 3.84, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', 17.00, '', '', '', '', '', '', '', '', '', '', '', '', 17.00, '', '', '', '', '', '', ''),
                ('', '', '', '', '', 1.76, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', 16.00, '', '', '', '', '', '', '', '', '', 16.00, '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', 3.20, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', 15.00, '', '', '', '', '', '', '', 15.00, '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 14.00, ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', -1.71, '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 1.39, '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', -1.49, '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 1.28, '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', -1.20, '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 1.10, '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', -0.40, '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0.40, '', '', '', ''),
                ('04', '85', 'OTE2003102G1', 'MEX', 16.00, 1.76, 20.00, 2.40, 32.00, 7.04, 18.00, 4.16, 19.00, 4.48, 16.00, 20.00, 15.00, 18.00, 19.00, '', '', 17.00, '', '', -0.63, '', '', 14.00, ''),

                ('05', '85', '12-3456789', 'USA', 16.00, 1.76, 20.00, 2.40, 32.00, 7.04, 18.00, 4.16, 19.00, 4.48, 16.00, 20.00, 15.00, 18.00, 19.00, '', '', 17.00, '', '', -0.63, '', '', 14.00, ''),
                ('', '', '', '', '', '', '', 2.40, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', 20.00, '', '', '', '', '', '', '', '', 20.00, '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', 4.48, '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', 19.00, '', '', '', '', '', 19.00, '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', 4.16, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', 18.00, '', '', '', '', '', '', 18.00, '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', 3.84, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', 17.00, '', '', '', '', '', '', '', '', '', '', '', '', 17.00, '', '', '', '', '', '', ''),
                ('', '', '', '', '', 1.76, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', 16.00, '', '', '', '', '', '', '', '', '', 16.00, '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', 3.20, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', 15.00, '', '', '', '', '', '', '', 15.00, '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 14.00, ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', -1.71, '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 1.39, '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', -1.49, '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 1.28, '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', -1.20, '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 1.10, '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', -0.40, '', '', '', ''),
                ('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0.40, '', '', '', ''),
                ('05', '85', '12-3456789', 'USA', 16.00, 1.76, 20.00, 2.40, 32.00, 7.04, 18.00, 4.16, 19.00, 4.48, 16.00, 20.00, 15.00, 18.00, 19.00, '', '', 17.00, '', '', -0.63, '', '', 14.00, ''),

                ('', '', '', '', 32.00, 3.52, 40.00, 4.80, 64.00, 14.08, 36.00, 8.32, 38.00, 8.96, 32.00, 40.00, 30.00, 36.00, 38.00, '', '', 34.00, '', '', -1.26, '', '', 28.00, ''),
                ]
        )

        self.assertEqual(
            self.env[diot_report.custom_handler_model_name].action_get_diot_txt(options)['file_content'].decode(),
            "04|85|OTE2003102G1|||||16|2|20|2|32|7|18|4|19|4|16||20||15||18||19||||||||||17||||||||||||-1|||14|||01\n"
            "05|85||12-3456789|partnerb|USA||16|2|20|2|32|7|18|4|19|4|16||20||15||18||19||||||||||17||||||||||||-1|||14|||01"
        )

        self.assertEqual(
            self.env[diot_report.custom_handler_model_name].action_get_dpiva_txt(options)['file_content'].decode(),
            "|1.0|2022|MES|Enero|1|1|||22|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|04|85|OTE2003102G1|||||15|||16|||18|||||14||-1|13|\n"
            "|1.0|2022|MES|Enero|1|1|||22|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|05|85||12-3456789|partnerb|USA|American|15|||16|||18|||||14||-1|13|"
        )

        # Testing a Bill with 2+ taxes on the same line
        multi_taxes = self.env['account.tax']
        multi_taxes += self.env.ref(f'l10n_mx.{self.env.company.id}_tax14')  # IVA(16%) COMPRAS
        multi_taxes += self.env.ref(f'l10n_mx.{self.env.company.id}_tax1')  # RET IVA FLETES 4%
        multi_taxes += self.env.ref(f'l10n_mx.{self.env.company.id}_tax2')  # RET IVA ARRENDAMIENTO 10%

        multi_tax_line_move = self.env['account.move'].create({
             'move_type': 'in_invoice',
             'partner_id': self.partner_a.id,
             'invoice_payment_term_id': False,
             'invoice_date': date_invoice,
             'date': date_invoice,
             'invoice_line_ids': [Command.create({
                 'name': 'test multi tax',
                 'quantity': 1,
                 'price_unit': 100,
                 'tax_ids': [Command.set(multi_taxes.ids)],
             })]
        })
        multi_tax_line_move.action_post()

        self.env['account.payment.register'].with_context(active_model='account.move', active_ids=multi_tax_line_move.ids).create({
            'payment_date': date_invoice,
            'journal_id': self.company_data['default_journal_bank'].id,
            'amount': multi_tax_line_move.amount_total,
        })._create_payments()

        options = self._generate_options(diot_report, fields.Date.from_string('2022-01-01'), fields.Date.from_string('2022-12-31'))

        self.assertLinesValues(
            diot_report._get_lines(options),
            # 1-4: partner info
            # 5-6: 8% N./refund, 7-8: 8% N./refund, 9-10: 16%/refund, 11-12: 16% imp/refund, 13-14: 16% int_imp/refund
            # 15-19: creditable in same order, 20-24: non-creditable in same order
            # 25: withheld, 26: exempt, 27: exempt imports, 28: 0%, 29: no tax object
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
            [
                ('', '', '', '', 32.00, 3.52, 40.00, 4.80, 164.00, 14.08, 36.00, 8.32, 38.00, 8.96, 32.00, 40.00, 130.00, 36.00, 38.00, '', '', 34.00, '', '', 12.74, '', '', 28.00, ''),
                ('04', '85', 'OTE2003102G1', 'MEX', 16.00, 1.76, 20.00, 2.40, 132.00, 7.04, 18.00, 4.16, 19.00, 4.48, 16.00, 20.00, 115.00, 18.00, 19.00, '', '', 17.00, '', '', 13.37, '', '', 14.00, ''),
                ('05', '85', '12-3456789', 'USA', 16.00, 1.76, 20.00, 2.40, 32.00, 7.04, 18.00, 4.16, 19.00, 4.48, 16.00, 20.00, 15.00, 18.00, 19.00, '', '', 17.00, '', '', -0.63, '', '', 14.00, ''),
                ('', '', '', '', 32.00, 3.52, 40.00, 4.80, 164.00, 14.08, 36.00, 8.32, 38.00, 8.96, 32.00, 40.00, 130.00, 36.00, 38.00, '', '', 34.00, '', '', 12.74, '', '', 28.00, ''),
            ]
        )

        self.assertEqual(
            self.env[diot_report.custom_handler_model_name].action_get_diot_txt(options)['file_content'].decode(),
            "04|85|OTE2003102G1|||||16|2|20|2|132|7|18|4|19|4|16||20||115||18||19||||||||||17||||||||||||13|||14|||01\n"
            "05|85||12-3456789|partnerb|USA||16|2|20|2|32|7|18|4|19|4|16||20||15||18||19||||||||||17||||||||||||-1|||14|||01"
        )

    def test_diot_report_with_refund(self):
        date_invoice = '2022-07-01'
        tax = self.purchase_taxes.filtered(lambda tax: tax.name == "IVA 16% COMPRAS")

        move = self.env['account.move'].create({
            'move_type': 'in_refund',
            'partner_id': self.partner_a.id,
            'invoice_date': date_invoice,
            'date': date_invoice,
            'invoice_line_ids': [Command.create({
                'name': f'test {tax.amount}',
                'quantity': 1,
                'price_unit': 100,
                'tax_ids': [Command.set(tax.ids)],
            })]
        })
        move.action_post()

        self.env['account.payment.register'].with_context(active_model='account.move', active_ids=move.ids).create({
                'payment_date': date_invoice,
                'journal_id': self.company_data['default_journal_bank'].id,
                'amount': move.amount_total,
            })._create_payments()

        self.assertTrue(move.payment_state in ('paid', 'in_payment'))

        diot_report = self.env.ref('l10n_mx_reports.diot_report')

        options = self._generate_options(diot_report, fields.Date.from_string('2022-01-01'), fields.Date.from_string('2022-12-31'))

        # Requires a complete redo
        self.assertLinesValues(
            diot_report._get_lines(options),
            # 1-4: partner information, 9: 16% total, 10: 16% refunds
            [1, 2, 3, 4, 9, 10],
            [
                ('', '', '', '', '', 16.00),
                ('04', '85', 'OTE2003102G1', 'MEX', '', 16.00),
                ('', '', '', '', '', 16.00),
            ]
        )

        self.assertEqual(
            self.env[diot_report.custom_handler_model_name].action_get_diot_txt(options)['file_content'].decode(),
            "04|85|OTE2003102G1||||||||||16|||||||||||||||||||||||||||||||||||||||||01")

        self.assertEqual(
            self.env[diot_report.custom_handler_model_name].action_get_dpiva_txt(options)['file_content'].decode(),
            "|1.0|2022|MES|Enero|1|1|||1|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|04|85|OTE2003102G1|||||||||||||||||||16|")
