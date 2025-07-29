# Part of Odoo. See LICENSE file for full copyright and licensing details.
# pylint: disable=C0326

from freezegun import freeze_time
from odoo import Command
from odoo.tests import tagged
from odoo.tools.misc import NON_BREAKING_SPACE
from odoo.addons.account_reports.tests.common import TestAccountReportsCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class GermanyBalanceSheetReportTest(TestAccountReportsCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass('l10n_de_skr03.l10n_de_chart_template')
        cls.company = cls.company_data['company']
        cls.report = cls.env.ref('l10n_de_reports.balance_sheet_l10n_de')

    @freeze_time('2025-03-17')
    def test_balance_sheet_unaffected_carry_over(self):
        _invoice_1 = self.init_invoice('out_invoice', invoice_date='2024-03-17', post=True, amounts=[1000])
        _invoice_2 = self.init_invoice('out_invoice', invoice_date='2025-03-17', post=True, amounts=[1000])

        options = self.report._get_options({'date': {'mode': 'range', 'filter': 'this_year'}, 'comparison': {'filter': 'previous_period', 'number_period': 1}})

        expected_lines = [
            # name                                                                                        2025                                  2024
            ('Aktivseite',                                                    f'2,000.00{NON_BREAKING_SPACE}€',     f'1,000.00{NON_BREAKING_SPACE}€'),
            ('A. Anlagevermögen',                                                                           '',                                   ''),
            ('I. Immaterielle Vermögensgegenstände',                                                        '',                                   ''),
            ('1. Selbst geschaffene gewerbliche Schutzrechte und ähnliche Rechte und Werte',                '',                                   ''),
            ('2. Konzessionen, Lizenzen und ähnliche Rechte und Werte',                                     '',                                   ''),
            ('3. Geschäfts- oder Firmenwert',                                                               '',                                   ''),
            ('4. geleistete Anzahlungen',                                                                   '',                                   ''),
            ('II. Sachanlagen',                                                                             '',                                   ''),
            ('1. Grundstücke. grundstücksgleiche Rechte und Bauten',                                        '',                                   ''),
            ('2. Technische  Anlagen und Maschinen',                                                        '',                                   ''),
            ('3. Andere Anlagen. Betriebs- und Geschäftsausstattung',                                       '',                                   ''),
            ('4. Geleistete Anzahlungen und Anlagen im Bau',                                                '',                                   ''),
            ('III. Finanzanlagen',                                                                          '',                                   ''),
            ('1. Anteile an verbundenen Unternehmen',                                                       '',                                   ''),
            ('2. Ausleihungen an verbundene Unternehmen',                                                   '',                                   ''),
            ('3. Beteiligungen',                                                                            '',                                   ''),
            ('4. Ausleihungen an Unternehmen, mit denen ein Beteiligungsverhältnis besteht',                '',                                   ''),
            ('5. Wertpapiere des Anlagevermögens',                                                          '',                                   ''),
            ('6. sonstige Ausleihungen',                                                                    '',                                   ''),
            ('B. Umlaufvermögen',                                             f'2,000.00{NON_BREAKING_SPACE}€',     f'1,000.00{NON_BREAKING_SPACE}€'),
            ('I. Vorräte',                                                                                  '',                                   ''),
            ('1. Roh-, Hilfs- und Betriebsstoffe',                                                          '',                                   ''),
            ('2. Unfertige Erzeugnisse, unfertige Leistungen',                                              '',                                   ''),
            ('3. Fertige Erzeugnisse und Waren',                                                            '',                                   ''),
            ('4. Geleistete Anzahlungen',                                                                   '',                                   ''),
            ('II. Forderungen und sonstige Vermögensgegenstände',             f'2,000.00{NON_BREAKING_SPACE}€',     f'1,000.00{NON_BREAKING_SPACE}€'),
            ('1. Forderungen aus Lieferungen und Leistungen',                 f'2,380.00{NON_BREAKING_SPACE}€',     f'1,190.00{NON_BREAKING_SPACE}€'),
            ('2. Forderungen gegen verbundene Unternehmen',                                                 '',                                   ''),
            ('3. Forderungen gegen Unternehmen, mit denen ein Beteiligungsverhältnis besteht',              '',                                   ''),
            ('4. Sonstige Vermögensgegenstände',                               f'-380.00{NON_BREAKING_SPACE}€',      f'-190.00{NON_BREAKING_SPACE}€'),
            ('III. Wertpapiere',                                                                            '',                                   ''),
            ('1. Anteile an verbundenen Unternehmen',                                                       '',                                   ''),
            ('2. sonstige Wertpapiere',                                                                     '',                                   ''),
            ('IV. Kassenbestand, Bundesbankguthaben, Guthaben bei Kreditinstituten und Schecks',            '',                                   ''),
            ('C. Rechnungsabgrenzungsposten',                                                               '',                                   ''),
            ('D. Aktive latente Steuern',                                                                   '',                                   ''),
            ('E. Aktiver Unterschiedsbetrag aus der Vermögensverrechnung',                                  '',                                   ''),
            ('Passivseite',                                                   f'2,000.00{NON_BREAKING_SPACE}€',     f'1,000.00{NON_BREAKING_SPACE}€'),
            ('A. Eigenkapital',                                               f'2,000.00{NON_BREAKING_SPACE}€',     f'1,000.00{NON_BREAKING_SPACE}€'),
            ('I. Gezeichnetes Kapital',                                                                     '',                                   ''),
            ('II. Kapitalrücklage',                                                                         '',                                   ''),
            ('III. Gewinnrücklagen',                                                                        '',                                   ''),
            ('1. Gesetzliche Rücklage',                                                                     '',                                   ''),
            ('2. Rücklage für Anteile an einem herrschenden oder mehrheitlich beteiligten Unternehmen',     '',                                   ''),
            ('3. Satzungsmäßige Rücklagen',                                                                 '',                                   ''),
            ('4. Andere Gewinnrücklagen',                                                                   '',                                   ''),
            ('IV. Gewinnvortrag/Verlustvortrag',                              f'1,000.00{NON_BREAKING_SPACE}€',                                   ''),
            ('V. Jahresüberschuß/Jahresfehlbetrag',                           f'1,000.00{NON_BREAKING_SPACE}€',     f'1,000.00{NON_BREAKING_SPACE}€'),
            ('B. Rückstellungen',                                                                           '',                                   ''),
            ('1. Rückstellungen für Pensionen und ähnliche Verpflichtungen',                                '',                                   ''),
            ('2. Steuerrückstellungen',                                                                     '',                                   ''),
            ('3. Sonstige Rückstellungen',                                                                  '',                                   ''),
            ('C. Verbindlichkeiten',                                                                        '',                                   ''),
            ('1. Anleihen, davon konvertibeln',                                                             '',                                   ''),
            ('2. Verbindlichkeiten gegenüber Kreditinstituten',                                             '',                                   ''),
            ('3. Erhaltene Anzahlungen auf Bestellungen',                                                   '',                                   ''),
            ('4. Verbindlichkeiten aus Lieferungen und Leistungen',                                         '',                                   ''),
            ('5. Verbindlichkeiten aus der Annahme gezogener Wechsel und der Ausstellung eigener Wechsel',  '',                                   ''),
            ('6. Verbindlichkeiten gegenüber verbundenen Unternehmen',                                      '',                                   ''),
            ('7. Verbindlichkeiten gegenüber Unternehmen, mit denen ein Beteiligungsverhältnis besteht',    '',                                   ''),
            ('8. Sonstige Verbindlichkeiten, davon aus Steuern, davon im Rahmen der sozialen Sicherheit',   '',                                   ''),
            ('D. Rechnungsabgrenzungsposten',                                                               '',                                   ''),
            ('E. Passive latente Steuern',                                                                  '',                                   ''),
        ]

        self.assertLinesValues(
            self.report._get_lines(options),
            # name, 2025, 2024
            [0, 1, 2],
            expected_lines,
        )

        equity_unaffected_account = self.env['account.account'].search([('account_type', '=', 'equity_unaffected')], limit=1)
        equity_account = self.env['account.account'].search([('account_type', '=', 'equity')], limit=1)
        closing_entry = self.env['account.move'].create({
            'move_type': 'entry',
            'date': '2024-12-31',
            'line_ids': [
                Command.create({
                    'account_id': equity_unaffected_account.id,
                    'debit': 1000,
                }),
                Command.create({
                    'account_id': equity_account.id,
                    'credit': 1000,
                })
            ]
        })
        closing_entry.action_post()

        expected_lines[39] = ('I. Gezeichnetes Kapital', f'1,000.00{NON_BREAKING_SPACE}€', f'1,000.00{NON_BREAKING_SPACE}€')
        expected_lines[46] = ('IV. Gewinnvortrag/Verlustvortrag', '', '')
        expected_lines[47] = ('V. Jahresüberschuß/Jahresfehlbetrag', f'1,000.00{NON_BREAKING_SPACE}€', '')

        self.assertLinesValues(
            self.report._get_lines(options),
            # name, 2024, 2025
            [0, 1, 2],
            expected_lines,
        )
