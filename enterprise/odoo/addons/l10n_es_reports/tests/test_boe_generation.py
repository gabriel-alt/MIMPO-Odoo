# -*- coding: utf-8 -*-

from freezegun import freeze_time

from odoo.addons.l10n_es_reports.tests.common import TestEsAccountReportsCommon
from odoo import fields
from odoo.tests import tagged


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestBOEGeneration(TestEsAccountReportsCommon):
    """ Basic tests checking the generation of BOE files is still possible.
    """

    def _check_boe_111_to_303(self, modelo_number):
        self.init_invoice('out_invoice', partner=self.spanish_partner, amounts=[10000], invoice_date=fields.Date.today(), taxes=self.spanish_test_tax, post=True)
        report = self.env.ref('l10n_es_reports.mod_%s' % modelo_number)
        options = self._generate_options(report, fields.Date.from_string('2020-12-01'), fields.Date.from_string('2020-12-31'))
        if 'multi_company' in options:
            del options['multi_company']
        self._check_boe_export(report, options, modelo_number)

    @freeze_time('2020-12-22')
    def test_boe_mod_111(self):
        self._check_boe_111_to_303('111')

    @freeze_time('2020-12-22')
    def test_boe_mod_115(self):
        self._check_boe_111_to_303('115')

    @freeze_time('2020-12-22')
    def test_boe_mod_303(self):
        self._check_boe_111_to_303('303')

    @freeze_time('2020-12-22')
    def test_boe_mod_347(self):
        invoice = self.init_invoice('out_invoice', partner=self.spanish_partner, amounts=[10000], invoice_date=fields.Date.today())
        invoice.l10n_es_reports_mod347_invoice_type = 'regular'
        invoice._post()
        report = self.env.ref('l10n_es_reports.mod_347')
        options = self._generate_options(report, fields.Date.from_string('2020-01-01'), fields.Date.from_string('2020-12-31'))
        if 'multi_company' in options:
            del options['multi_company']
        self._check_boe_export(report, options, 347)

    @freeze_time('2020-12-22')
    def test_boe_mod_349(self):
        self.partner_a.write({
            'country_id': self.env.ref('base.be').id,
            'vat': "BE0477472701",
        })
        invoice = self.init_invoice('out_invoice', partner=self.partner_a, amounts=[10000], invoice_date=fields.Date.today())
        invoice.l10n_es_reports_mod349_invoice_type = 'E'
        invoice._post()
        report = self.env.ref('l10n_es_reports.mod_349')
        options = self._generate_options(report, fields.Date.from_string('2020-12-01'), fields.Date.from_string('2020-12-31'))
        if 'multi_company' in options:
            del options['multi_company']
        self._check_boe_export(report, options, 349)

    @freeze_time('2025-05-15')
    def test_boe_includes_null_lines_mod_349(self):
        """
        Test that the mod 349 boe report contains the rectification lines even when the total rectification sum to 0
        """
        partner = self.env['res.partner'].create({
            'name': 'Test',
            'company_id': self.company_data['company'].id,
            'company_type': 'company',
            'country_id': self.env['res.country'].search([('code', '=', 'BE')]).id,
            'vat': 'BE0477472701',
        })
        invoice = self.init_invoice('out_invoice', partner=partner, amounts=[1000], invoice_date='2025-03-15')
        invoice.action_post()

        credit_note_wizard = self.env['account.move.reversal'].with_context({
            'active_ids': invoice.id,
            'active_id': invoice.id,
            'active_model': 'account.move',
        }).create({
            'refund_method': 'modify',
            'reason': 'modify',
            'journal_id': invoice.journal_id.id,
        })
        credit_note_wizard.reverse_moves()

        report = self.env.ref('l10n_es_reports.mod_349')
        options = self._generate_options(report, fields.Date.from_string('2025-05-01'), fields.Date.from_string('2025-05-31'))
        wizard_action = self.env['l10n_es.mod349.tax.report.handler'].open_boe_wizard(options, '349')
        options['l10n_es_reports_boe_wizard_id'] = wizard_action['res_id']

        boe_file = self.env['l10n_es.mod349.tax.report.handler'].export_boe(options)

        # This string represents a rectification record included in the BOE export.
        # It contains:
        # - the year (2025),
        # - the period,
        # - the rectified tax base (0.00),
        # - and the previously declared tax base (1000.00).
        # Under REGISTRO DE RECTIFICACIONES https://www.boe.es/buscar/doc.php?id=BOE-A-2010-5098
        self.assertIn('20250300000000000000000000100000', boe_file['file_content'].decode('utf-8'))

    @freeze_time('2025-05-15')
    def test_boe_excludes_current_period_rectification_lines(self):
        """
        Test that moves from the current period are not included as rectification lines in the boe report
        """
        partner = self.env['res.partner'].create({
            'name': 'Test',
            'company_id': self.company_data['company'].id,
            'company_type': 'company',
            'country_id': self.env['res.country'].search([('code', '=', 'BE')]).id,
            'vat': 'BE0477472701',
        })
        previous_period_invoice = self.init_invoice('out_invoice', partner=partner, amounts=[1000], invoice_date='2025-03-15')
        previous_period_invoice.action_post()

        credit_note_wizard_previous = self.env['account.move.reversal'].with_context({
            'active_ids': previous_period_invoice.id,
            'active_id': previous_period_invoice.id,
            'active_model': 'account.move',
        }).create({
            'refund_method': 'modify',
            'reason': 'modify',
            'journal_id': previous_period_invoice.journal_id.id,
        })
        credit_note_wizard_previous.reverse_moves()

        current_period_invoice = self.init_invoice('out_invoice', partner=partner, amounts=[1000], invoice_date='2025-05-15')
        current_period_invoice.action_post()

        credit_note_wizard_current = self.env['account.move.reversal'].with_context({
            'active_ids': current_period_invoice.id,
            'active_id': current_period_invoice.id,
            'active_model': 'account.move',
        }).create({
            'refund_method': 'modify',
            'reason': 'modify',
            'journal_id': current_period_invoice.journal_id.id,
        })
        credit_note_wizard_current.reverse_moves()

        report = self.env.ref('l10n_es_reports.mod_349')
        options = self._generate_options(report, fields.Date.from_string('2025-05-01'), fields.Date.from_string('2025-05-31'))
        wizard_action = self.env['l10n_es.mod349.tax.report.handler'].open_boe_wizard(options, '349')
        options['l10n_es_reports_boe_wizard_id'] = wizard_action['res_id']

        boe_file = self.env['l10n_es.mod349.tax.report.handler'].export_boe(options)
        # This string represents a rectification record included in the BOE export.
        # It contains:
        # - the year (2025),
        # - the period (here 5 which is the current period),
        # - the rectified tax base (0.00),
        # - and the previously declared tax base (1000.00).
        # Under REGISTRO DE RECTIFICACIONES https://www.boe.es/buscar/doc.php?id=BOE-A-2010-5098
        self.assertNotIn('20250500000000000000000000100000', boe_file['file_content'].decode('utf-8'))
