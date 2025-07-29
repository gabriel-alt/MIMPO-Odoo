
from odoo.addons.account_reports.tests.common import TestAccountReportsCommon

class TestEsAccountReportsCommon(TestAccountReportsCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref='l10n_es.account_chart_template_pymes')

        cls.spanish_partner = cls.env['res.partner'].create({
            'name': "Bernardo Ganador",
            'street': "Avenida de los Informes Financieros, 42",
            'zip': 4242,
            'city': "Madrid",
            'country_id': cls.env.ref('base.es').id,
            'state_id': cls.env.ref('base.state_es_m').id,
            'vat': "ESA12345674",
        })

        base_tags = cls.env.ref('l10n_es.mod_111_02') + cls.env.ref('l10n_es.mod_115_02') + cls.env.ref('l10n_es.mod_303_01')
        tax_tags = cls.env.ref('l10n_es.mod_111_03') + cls.env.ref('l10n_es.mod_115_03') + cls.env.ref('l10n_es.mod_303_03')
        cls.spanish_test_tax = cls.env['account.tax'].create({
            'name': "Test ES BOE tax",
            'amount_type': 'percent',
            'amount': 42,
            'invoice_repartition_line_ids': [
                (0, 0, {
                    'repartition_type': 'base',
                    'tag_ids': base_tags.ids,
                }),

                (0, 0, {
                    'repartition_type': 'tax',
                    'tag_ids': tax_tags.ids,
                })
            ],
            'refund_repartition_line_ids': [
                (0, 0, {
                    'repartition_type': 'base',
                    'tag_ids': base_tags.ids,
                }),

                (0, 0, {
                    'repartition_type': 'tax',
                    'tag_ids': tax_tags.ids,
                })
            ],
        })

        cls.env.company.vat = "ESA12345674"

    def _check_boe_export(self, report, options, modelo_number):
        wizard_action = self.env[report.custom_handler_model_name].open_boe_wizard(options, modelo_number)
        self.assertEqual(f'l10n_es_reports.aeat.boe.mod{modelo_number}.export.wizard', wizard_action['res_model'], "Wrong BOE export wizard returned")
        options['l10n_es_reports_boe_wizard_id'] = wizard_action['res_id']
        self.assertTrue(self.env[report.custom_handler_model_name].export_boe(options), "Empty BOE")
