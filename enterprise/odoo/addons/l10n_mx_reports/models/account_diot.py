# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from __future__ import division

import re
import logging
from unicodedata import normalize


from odoo import _, fields, models
from odoo.exceptions import RedirectWarning, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, get_lang

_logger = logging.getLogger(__name__)


def diot_country_adapt(values):
    # 2025 SAT classification uses 3-letter country codes
    # https://www.fiscalia.com/archivos/2025-02-06-DIOT_2025_Ayuda_Carga_Masiva.pdf
    cc = values.get('country_code')
    diot_country_dict = {
        'MX': 'MEX', None: '',
        'AF': 'AFG', 'AX': 'ALA', 'AL': 'ALB', 'DE': 'DEU', 'AD': 'AND', 'AO': 'AGO', 'AI': 'AIA', 'AQ': 'ATA', 'AG': 'ATG', 'SA': 'SAU',
        'DZ': 'DZA', 'AR': 'ARG', 'AM': 'ARM', 'AW': 'ABW', 'AU': 'AUS', 'AT': 'AUT', 'AZ': 'AZE', 'BS': 'BHS', 'BD': 'BGD', 'BB': 'BRB',
        'BH': 'BHR', 'BE': 'BEL', 'BZ': 'BLZ', 'BJ': 'BEN', 'BM': 'BMU', 'BY': 'BLR', 'MM': 'MMR', 'BO': 'BOL', 'BA': 'BIH', 'BW': 'BWA',
        'BR': 'BRA', 'BN': 'BRN', 'BG': 'BGR', 'BF': 'BFA', 'BI': 'BDI', 'BT': 'BTN', 'CV': 'CPV', 'KH': 'KHM', 'CM': 'CMR', 'CA': 'CAN',
        'QA': 'QAT', 'TD': 'TCD', 'CL': 'CHL', 'CN': 'CHN', 'CY': 'CYP', 'CO': 'COL', 'KM': 'COM', 'KP': 'PRK', 'KR': 'KOR', 'CI': 'CIV',
        'CR': 'CRI', 'HR': 'HRV', 'CU': 'CUB', 'CW': 'CUW', 'DK': 'DNK', 'DM': 'DMA', 'EC': 'ECU', 'EG': 'EGY', 'SV': 'SLV', 'AE': 'ARE',
        'ER': 'ERI', 'SK': 'SVK', 'SI': 'SVN', 'ES': 'ESP', 'US': 'USA', 'EE': 'EST', 'ET': 'ETH', 'PH': 'PHL', 'FI': 'FIN', 'FJ': 'FJI',
        'FR': 'FRA', 'GA': 'GAB', 'GM': 'GMB', 'GE': 'GEO', 'GH': 'GHA', 'GI': 'GIB', 'GD': 'GRD', 'GR': 'GRC', 'GL': 'GRL', 'GP': 'GLP',
        'GU': 'GUM', 'GT': 'GTM', 'GF': 'GUF', 'GG': 'GGY', 'GN': 'GIN', 'GW': 'GNB', 'GQ': 'GNY', 'HT': 'HTI', 'HN': 'HND', 'HK': 'HKG',
        'HU': 'HUN', 'IN': 'IND', 'IQ': 'IRQ', 'IR': 'IRN', 'IE': 'IRL', 'BV': 'BVT', 'IM': 'IMN', 'CX': 'CXR', 'NF': 'NFK', 'IS': 'ISL',
        'KY': 'CYM', 'CC': 'CCK', 'CK': 'COK', 'FO': 'FRO', 'GS': 'SGS', 'HM': 'HMD', 'FK': 'FLK', 'MP': 'MNP', 'MH': 'MHL', 'PN': 'PCN',
        'SB': 'SLB', 'TC': 'TCA', 'UM': 'UMI', 'VG': 'VGB', 'VI': 'VIR', 'IL': 'ISR', 'IT': 'ITA', 'JM': 'JAM', 'JP': 'JPN', 'JE': 'JEY',
        'JO': 'JOR', 'KZ': 'KAZ', 'KE': 'KEN', 'KG': 'KGZ', 'KI': 'KIR', 'KW': 'KWT', 'LA': 'LAO', 'LS': 'LSO', 'LV': 'LVA', 'LB': 'LBA',
        'LR': 'LBR', 'LY': 'LBY', 'LI': 'LIE', 'LT': 'LTU', 'LU': 'LUX', 'MO': 'MAC', 'MG': 'MDG', 'MY': 'MYS', 'MW': 'MWI', 'MV': 'MDV',
        'ML': 'MLI', 'MT': 'MLT', 'MA': 'MAR', 'MQ': 'MTQ', 'MU': 'MUS', 'MR': 'MRT', 'YT': 'MYT', 'FM': 'FSM', 'MD': 'MDA', 'MC': 'MCO',
        'MN': 'MNG', 'ME': 'MNE', 'MS': 'MSR', 'MZ': 'MOZ', 'NA': 'NAM', 'NR': 'NRU', 'NP': 'NPL', 'NI': 'NIC', 'NE': 'NER', 'NG': 'NGA',
        'NU': 'NIU', 'NO': 'NOR', 'NC': 'NCL', 'NZ': 'NZL', 'OM': 'OMN', 'NL': 'NLD', 'PK': 'PAK', 'PW': 'PLW', 'PS': 'PSE', 'PA': 'PAN',
        'PG': 'PNG', 'PY': 'PRY', 'PE': 'PER', 'PF': 'PYF', 'PL': 'POL', 'PT': 'PRT', 'PR': 'PRI', 'CF': 'CAF', 'CZ': 'CZE', 'MK': 'MKD',
        'CG': 'COG', 'CD': 'COD', 'DR': 'DOM', 'RE': 'REU', 'RW': 'RWA', 'RO': 'ROU', 'RU': 'RUS', 'EH': 'ESH', 'WS': 'WSM', 'AS': 'ASM',
        'BL': 'BLM', 'KN': 'KNA', 'SM': 'SMR', 'MF': 'MAF', 'PM': 'SPM', 'VC': 'VCT', 'SH': 'SHN', 'LC': 'LCA', 'ST': 'STP', 'SN': 'SEN',
        'RS': 'SRB', 'SC': 'SYC', 'SL': 'SLE', 'SG': 'SGP', 'SX': 'SXM', 'SY': 'SYR', 'SO': 'SOM', 'LK': 'LKA', 'SZ': 'SWZ', 'ZA': 'ZAF',
        'SD': 'SDN', 'SS': 'SSD', 'SE': 'SWE', 'CH': 'CHE', 'SR': 'SUR', 'SJ': 'SJM', 'TH': 'THA', 'TW': 'TWA', 'TZ': 'TZA', 'TJ': 'TJK',
        'IO': 'IOT', 'TF': 'ATF', 'TL': 'TLS', 'TG': 'TGO', 'TK': 'TKL', 'TO': 'TON', 'TT': 'TTO', 'TN': 'TUN', 'TM': 'TKM', 'TR': 'TUR',
        'TV': 'TUV', 'UA': 'UKR', 'UG': 'UGA', 'UY': 'URY', 'UZ': 'UZB', 'VU': 'VUT', 'VA': 'VAT', 'VE': 'VEN', 'VN': 'VNM', 'WF': 'WLF',
        'YE': 'YEM', 'DJ': 'DJY', 'ZM': 'ZMB', 'ZW': 'ZWE'
    }

    if cc not in diot_country_dict:
        # Country not in DIOT catalog, so we use the special code 'ZZZ'
        # for 'Other' countries
        values['country_code'] = 'ZZZ'
    else:
        # Map the standard country_code to the SAT standard
        values['country_code'] = diot_country_dict.get(cc, cc)
    return values


class MexicanAccountReportCustomHandler(models.AbstractModel):
    _name = 'l10n_mx.report.handler'
    _inherit = 'account.report.custom.handler'
    _description = 'Mexican Account Report Custom Handler'

    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        options['columns'] = list(options['columns'])
        options.setdefault('buttons', []).extend((
            {'name': _('DIOT (txt)'), 'sequence': 40, 'action': 'export_file', 'action_param': 'action_get_diot_txt', 'file_export_type': _('DIOT')},
            {'name': _('DPIVA (txt)'), 'sequence': 60, 'action': 'export_file', 'action_param': 'action_get_dpiva_txt', 'file_export_type': _('DPIVA')},
        ))

    def _report_custom_engine_diot_report(self, expressions, options, date_scope, current_groupby, next_groupby, offset=0, limit=None):
        def build_dict(report, current_groupby, query_res):
            if not current_groupby:
                return query_res[0] if query_res else {k: None for k in report.mapped('line_ids.expression_ids.label')}
            return [(group_res["grouping_key"], group_res) for group_res in query_res]

        report = self.env['account.report'].browse(options['report_id'])
        query_res = self._execute_query(report, current_groupby, options, offset, limit)
        return build_dict(report, current_groupby, query_res)

    def _execute_query(self, report, current_groupby, options, offset, limit):
        report._check_groupby_fields([current_groupby] if current_groupby else [])

        cash_basis_journal_ids = self.env.companies.filtered('tax_cash_basis_journal_id').tax_cash_basis_journal_id
        tables, where_clause, where_params = report._query_get(options, 'strict_range', domain=[
            ('parent_state', '=', 'posted'),
            ('journal_id', 'in', cash_basis_journal_ids.ids),
            ('move_id.reversal_move_id', '=', False),
            ('move_id.reversed_entry_id', '=', False),
        ])

        # Creditable
        tag_8_n = self.env.ref('l10n_mx.tag_diot_8')
        tag_8_s = self.env.ref('l10n_mx.tag_diot_8_south')
        tag_16 = self.env.ref('l10n_mx.tag_diot_16')
        tag_16_imp = self.env.ref('l10n_mx.tag_diot_16_imp')
        tag_16_imp_int = self.env.ref('l10n_mx.tag_diot_16_imp_int')
        # Non-creditable
        tag_8_n_nc = self.env.ref('l10n_mx.tag_diot_8_non_cre', raise_if_not_found=False) or self.env['account.account.tag']
        tag_8_s_nc = self.env.ref('l10n_mx.tag_diot_8_south_non_cre', raise_if_not_found=False) or self.env['account.account.tag']
        tag_16_nc = self.env.ref('l10n_mx.tag_diot_16_non_cre', raise_if_not_found=False) or self.env['account.account.tag']
        tag_16_imp_nc = self.env.ref('l10n_mx.tag_diot_16_imp_non_cre', raise_if_not_found=False) or self.env['account.account.tag']
        tag_16_imp_int_nc = self.env.ref('l10n_mx.tag_diot_16_imp_int_non_cre', raise_if_not_found=False) or self.env['account.account.tag']
        # Refunds
        tag_8_n_r = self.env.ref('l10n_mx.tag_diot_8_refund')
        tag_8_s_r = self.env.ref('l10n_mx.tag_diot_8_south_refund')
        tag_16_r = self.env.ref('l10n_mx.tag_diot_16_refund')
        tag_16_imp_r = self.env.ref('l10n_mx.tag_diot_16_imp_refund')
        tag_16_imp_int_r = self.env.ref('l10n_mx.tag_diot_16_imp_int_refund')
        # Other
        tag_ret = self.env.ref('l10n_mx.tag_diot_ret')
        tag_exe = self.env.ref('l10n_mx.tag_diot_exento')
        tag_exe_imp = self.env.ref('l10n_mx.tag_diot_exento_imp')
        tag_0 = self.env.ref('l10n_mx.tag_diot_0')
        tag_no_obj = self.env.ref('l10n_mx.tag_diot_no_obj')

        diot_tags = (tag_8_n | tag_8_n_nc | tag_8_s | tag_8_s_nc | tag_16 | tag_16_nc | tag_16_imp | tag_16_imp_nc |
                     tag_16_imp_int | tag_16_imp_int_nc | tag_exe | tag_exe_imp | tag_0 | tag_no_obj)
        diot_tags_refunds = (tag_8_n_r | tag_8_s_r | tag_16_r | tag_16_imp_r | tag_16_imp_int_r)
        diot_tags_all = diot_tags + diot_tags_refunds

        raw_results_select_list = []
        lang = self.env.user.lang or get_lang(self.env).code
        if current_groupby == 'partner_id':
            raw_results_select_list.append(f'''
                CASE
                   WHEN partner.l10n_mx_type_of_operation = '87' THEN '15'
                   WHEN country.code = 'MX' THEN '04'
                   ELSE '05'
                END AS third_party_code,
                partner.l10n_mx_type_of_operation AS operation_type_code,
                partner.vat AS partner_vat_number,
                country.code AS country_code,
                COALESCE(country.demonym->>'{lang}', country.demonym->>'en_US') AS partner_nationality,
           ''')
        else:
            raw_results_select_list.append('''
                NULL AS third_party_code,
                NULL AS operation_type_code,
                NULL AS partner_vat_number,
                NULL AS country_code,
                NULL AS partner_nationality,
            ''')

        tag_columns = (
            'paid_8_n', 'paid_8_n_nc',
            'paid_8_s', 'paid_8_s_nc',
            'paid_16', 'paid_16_nc',
            'paid_16_imp', 'paid_16_imp_nc',
            'paid_16_imp_int', 'paid_16_imp_int_nc',
            'exempt', 'exempt_imp', 'paid_0', 'no_obj'
        )
        tag_columns_refunds = (
            'refund_8_n',
            'refund_8_s',
            'refund_16',
            'refund_16_imp',
            'refund_16_imp_int',
        )
        tail_query, tail_params = report._get_engine_query_tail(offset, limit)

        withholding_taxes = self.env['account.tax.repartition.line'].search([('tag_ids', 'in', tag_ret.id)]).tax_id
        withholding_taxes_query = ""
        withholding_taxes_params = []
        if withholding_taxes:
            withholding_taxes_query = f"""
                UNION ALL

                SELECT
                    {f'account_move_line.{current_groupby}' if current_groupby else 'NULL'} AS grouping_key,
                    {''.join(raw_results_select_list)}
                    {', '.join(f'0 AS {column}' for column in tag_columns)},
                    {', '.join(f'0 AS {column}' for column in tag_columns_refunds)},
                    -account_move_line.balance AS withheld
                FROM {tables}
                JOIN res_partner AS partner ON partner.id = account_move_line.partner_id
                LEFT JOIN res_country AS country ON country.id = partner.country_id
                WHERE {where_clause}
                AND tax_line_id IN %s
            """
            withholding_taxes_params = [*where_params, tuple(withholding_taxes.ids)]

        groupby_sql = """
            raw_results.grouping_key,
            raw_results.third_party_code,
            raw_results.operation_type_code,
            raw_results.partner_vat_number,
            raw_results.country_code,
            raw_results.partner_nationality
        """

        self._cr.execute(f"""
            WITH raw_results as (
                SELECT
                    {f'account_move_line.{current_groupby}' if current_groupby else 'NULL'} AS grouping_key,
                    {''.join(raw_results_select_list)}
                    {', '.join(f'CASE WHEN tag.id = %s THEN account_move_line.debit ELSE 0 END AS {column}' for column in tag_columns)},
                    {', '.join(f'CASE WHEN tag.id = %s THEN account_move_line.credit ELSE 0 END AS {column}' for column in tag_columns_refunds)},
                    0 AS withheld
                FROM {tables}
                JOIN account_account_tag_account_move_line_rel AS tag_aml_rel ON account_move_line.id = tag_aml_rel.account_move_line_id
                JOIN account_account_tag AS tag ON tag.id = tag_aml_rel.account_account_tag_id
                JOIN res_partner AS partner ON partner.id = account_move_line.partner_id
                LEFT JOIN res_country AS country ON country.id = partner.country_id
                WHERE {where_clause}
                AND tag.id IN %s

                {withholding_taxes_query}
            )
            SELECT
               raw_results.grouping_key AS grouping_key,
               count(raw_results.grouping_key) AS counter,
               raw_results.third_party_code AS third_party_code,
               raw_results.operation_type_code AS operation_type_code,
               COALESCE(raw_results.partner_vat_number, '') AS partner_vat_number,
               raw_results.country_code AS country_code,
               raw_results.partner_nationality AS partner_nationality,
               sum(raw_results.paid_8_n) AS paid_8_n,
               sum(raw_results.paid_8_s) AS paid_8_s,
               sum(raw_results.paid_16) AS paid_16,
               sum(raw_results.paid_16_imp) AS paid_16_imp,
               sum(raw_results.paid_16_imp_int) AS paid_16_imp_int,
               sum(raw_results.paid_8_n_nc) AS paid_8_n_nc,
               sum(raw_results.paid_8_s_nc) AS paid_8_s_nc,
               sum(raw_results.paid_16_nc) AS paid_16_nc,
               sum(raw_results.paid_16_imp_nc) AS paid_16_imp_nc,
               sum(raw_results.paid_16_imp_int_nc) AS paid_16_imp_int_nc,
               sum(raw_results.paid_8_n + raw_results.paid_8_n_nc) AS paid_8_n_wnc,
               sum(raw_results.paid_8_s + raw_results.paid_8_s_nc) AS paid_8_s_wnc,
               sum(raw_results.paid_16 + raw_results.paid_16_nc) AS paid_16_wnc,
               sum(raw_results.paid_16_imp + raw_results.paid_16_imp_nc) AS paid_16_imp_wnc,
               sum(raw_results.paid_16_imp_int + raw_results.paid_16_imp_int_nc) AS paid_16_imp_int_wnc,
               sum(raw_results.refund_8_n) AS refund_8_n,
               sum(raw_results.refund_8_s) AS refund_8_s,
               sum(raw_results.refund_16) AS refund_16,
               sum(raw_results.refund_16_imp) AS refund_16_imp,
               sum(raw_results.refund_16_imp_int) AS refund_16_imp_int,
               sum(raw_results.withheld) AS withheld,
               sum(raw_results.exempt) AS exempt,
               sum(raw_results.exempt_imp) AS exempt_imp,
               sum(raw_results.paid_0) AS paid_0,
               sum(raw_results.no_obj) AS no_obj,
               sum(raw_results.refund_8_n + raw_results.refund_8_s + raw_results.refund_16 + raw_results.refund_16_imp + raw_results.refund_16_imp_int) AS refunds
            FROM raw_results
            GROUP BY
                {groupby_sql}
            ORDER BY
                {groupby_sql}
           {tail_query}
            """,
            [
                *(diot_tags.ids),
                *(diot_tags_refunds.ids),
                *where_params,
                tuple(diot_tags_all.ids),
                *withholding_taxes_params,
                *tail_params,
            ]
        )

        return [diot_country_adapt(vals) for vals in self.env.cr.dictfetchall()]

    def action_get_diot_txt(self, options):
        report = self.env['account.report'].browse(options['report_id'])
        partner_and_values_to_report = {
            p: v for p, v in self._get_diot_values_per_partner(report, options).items()
            # don't report those for which all amount are 0
            if sum(v[x] for x in (
                'paid_8_n', 'paid_8_n_nc', 'refund_8_n',
                'paid_8_s', 'paid_8_s_nc', 'refund_8_s',
                'paid_16', 'paid_16_nc', 'refund_16',
                'paid_16_imp', 'paid_16_imp_nc', 'refund_16_imp',
                'paid_16_imp_int', 'paid_16_imp_int_nc', 'refund_16_imp_int',
                'withheld', 'exempt', 'exempt_imp', 'paid_0', 'no_obj'
            ))
        }

        self.check_for_error_on_partner(list(partner_and_values_to_report))

        lines = []
        data_87 = [0] * 54
        for partner, values in partner_and_values_to_report.items():
            if not sum(values[x] for x in (
                'paid_8_n', 'paid_8_n_nc', 'refund_8_n',
                'paid_8_s', 'paid_8_s_nc', 'refund_8_s',
                'paid_16', 'paid_16_nc', 'refund_16',
                'paid_16_imp', 'paid_16_imp_nc', 'refund_16_imp',
                'paid_16_imp_int', 'paid_16_imp_int_nc', 'refund_16_imp_int',
                'withheld', 'exempt', 'exempt_imp', 'paid_0', 'no_obj'
            )):
                # don't report if there isn't any amount to report
                continue

            data = [0] * 54
            if values['operation_type_code'] != '87':
                self.l10n_mx_diot_get_values(values, data, partner)
                for i in range(7, 53):
                    if not data[i]:
                        data[i] = ''
                    if not isinstance(data[i], str):
                        data[i] = str(round(data[i]))
                lines.append('|'.join(str(d) for d in data))
            else:
                self.l10n_mx_diot_get_values(values, data_87, partner)
        # Global Operations
        if any(data_87):
            for i in range(7, 53):
                if not data_87[i]:
                    data_87[i] = ''
                if not isinstance(data_87[i], str):
                    data_87[i] = str(round(data_87[i]))
            lines.append('|'.join(str(d) for d in data_87))

        diot_txt_result = '\n'.join(lines)
        return {
            'file_name': report.get_default_report_filename('txt'),
            'file_content': diot_txt_result.encode(),
            'file_type': 'txt',
        }

    def l10n_mx_diot_get_values(self, values, data, partner):
        is_foreign_partner = values['third_party_code'] != '04'
        is_global = values['operation_type_code'] == '87'
        # Non-numerical
        data[0] = values['third_party_code']  # Supplier Type
        data[1] = values['operation_type_code']  # Operation Type
        data[2] = 'XAXX010101000' if is_global else (values['partner_vat_number'] if not is_foreign_partner else '')  # Tax Number
        data[3] = '' if is_global else (values['partner_vat_number'] if is_foreign_partner else '')  # Tax Number for Foreigners
        data[4] = '' if is_global else (''.join(self.str_format(partner.name)).encode('utf-8').strip().decode('utf-8') if is_foreign_partner else '')  # Name
        data[5] = '' if is_global else (values['country_code'] if is_foreign_partner else '')  # Country
        data[6] = ''  # Fiscal Jurisdiction specified (for manual entry)
        # Sums and refunds
        data[7] += float(values['paid_8_n']) + float(values['paid_8_n_nc'])  # 8% Northern +NC paid
        data[8] += float(values['refund_8_n'])  # 8% Northern refunds
        data[9] += float(values['paid_8_s']) + float(values['paid_8_s_nc'])  # 8% Southern +NC paid
        data[10] += float(values['refund_8_s'])  # 8% Southern refunds
        data[11] += float(values['paid_16']) + float(values['paid_16_nc'])  # 16% +NC paid
        data[12] += float(values['refund_16'])  # 16% refunds
        data[13] += float(values['paid_16_imp']) + float(values['paid_16_imp_nc'])  # 16% imports +NC paid
        data[14] += float(values['refund_16_imp'])  # 16% imports refunds
        data[15] += float(values['paid_16_imp_int']) + float(values['paid_16_imp_int_nc'])  # 16% intangible imports +NC paid
        data[16] += float(values['refund_16_imp_int'])  # 16% int imp refunds
        # Creditable VAT
        data[17] += float(values['paid_8_n'])  # 8% Northern paid
        data[19] += float(values['paid_8_s'])  # 8% Southern paid
        data[21] += float(values['paid_16'])  # 16% VAT exclusive base
        data[23] += float(values['paid_16_imp'])  # 16% import VAT exclusive base
        data[25] += float(values['paid_16_imp_int'])  # 16% int imp VAT exclusive base
        # Non-creditable VAT
        data[27] += float(values['paid_8_n_nc'])  # 8% Northern NC paid
        data[31] += float(values['paid_8_s_nc'])  # 8% Southern NC paid
        data[35] += float(values['paid_16_nc'])  # 16% NC paid
        data[39] += float(values['paid_16_imp_nc'])  # 16% imports NC paid
        data[43] += float(values['paid_16_imp_int_nc'])  # 16% non tangible imports NC paid
        # Additional data
        data[47] += float(values['withheld'])  # DIOT:Retention base
        data[48] += float(values['exempt'])  # DIOT:Exempt base
        data[49] += float(values['exempt_imp'])  # DIOT:Import Exempt base
        data[50] += float(values['paid_0'])  # 0% payments
        data[51] += float(values['no_obj'])  # No tax object
        # Declaration
        data[53] = '02' if is_global else '01'  # "Hereby I declare that I rightfully credited VAT"

    def action_get_dpiva_txt(self, options):
        report = self.env['account.report'].browse(options['report_id'])
        partner_and_values_to_report = {
            p: v for p, v in self._get_diot_values_per_partner(report, options).items()
            # don't report those for which all amount are 0
            if sum(v[x] for x in (
                'paid_8_n', 'paid_16', 'paid_16_imp',
                'refund_8_n', 'refund_16', 'refund_16_imp',
                'paid_0', 'exempt', 'withheld'
            ))
        }

        self.check_for_error_on_partner(partner for partner in partner_and_values_to_report)

        date = fields.datetime.strptime(options['date']['date_from'], DEFAULT_SERVER_DATE_FORMAT)
        month = {
            '01': 'Enero',
            '02': 'Febrero',
            '03': 'Marzo',
            '04': 'Abril',
            '05': 'Mayo',
            '06': 'Junio',
            '07': 'Julio',
            '08': 'Agosto',
            '09': 'Septiembre',
            '10': 'Octubre',
            '11': 'Noviembre',
            '12': 'Diciembre',
        }.get(date.strftime("%m"))

        lines = []
        for partner, values in partner_and_values_to_report.items():
            if not sum(values[x] for x in (
                'paid_8_n', 'paid_16', 'paid_16_imp',
                'refund_8_n', 'refund_16', 'refund_16_imp',
                'paid_0', 'exempt', 'withheld'
            )):
                # don't report if there isn't any amount to report
                continue

            is_foreign_partner = values['third_party_code'] != '04'
            data = [''] * 48
            data[0] = '1.0'  # Version
            data[1] = f"{date.year}"  # Fiscal Year
            data[2] = 'MES'  # Cabling value
            data[3] = month  # Period
            data[4] = '1'  # 1 Because has data
            data[5] = '1'  # 1 = Normal, 2 = Complementary (Not supported now).
            data[8] = values['counter']  # Count the operations
            for num in range(9, 26):
                data[num] = '0'
            data[26] = values['third_party_code']  # Supplier Type
            data[27] = values['operation_type_code']  # Operation Type
            data[28] = values['partner_vat_number'] if not is_foreign_partner else ''  # Federal Taxpayer Registry Code
            data[29] = values['partner_vat_number'] if is_foreign_partner else ''  # Fiscal ID
            data[30] = ''.join(self.str_format(partner.name)).encode('utf-8').strip().decode('utf-8') if is_foreign_partner else ''  # Name
            data[31] = values['country_code'] if is_foreign_partner else ''  # Country
            data[32] = ''.join(self.str_format(values['partner_nationality'])).encode('utf-8').strip().decode('utf-8') if is_foreign_partner else ''  # Nationality
            data[33] = str(round(float(values['paid_16'])) or '')  # 16%
            data[36] = str(round(float(values['paid_8_n'])) or '')  # 8% (Nothern)
            data[39] = str(round(float(values['paid_16_imp'])) or '')  # 16% - Importation
            data[44] = str(round(float(values['paid_0'])) or '')  # 0%
            data[45] = str(round(float(values['exempt'])) or '')  # Exempt
            data[46] = str(round(float(values['withheld'])) or '')  # Withheld
            data[47] = str(round(float(values['refund_16']) + float(values['refund_8_n']) + float(values['refund_16_imp'])) or '')  # Refunds

            lines.append('|{}|'.format('|'.join(str(d) for d in data)))

        dpiva_txt_result = '\n'.join(lines)
        return {
            'file_name': report.get_default_report_filename('txt'),
            'file_content': dpiva_txt_result.encode(),
            'file_type': 'txt',
        }

    def _get_diot_values_per_partner(self, report, options):
        options['unfolded_lines'] = {}  # This allows to only get the first groupby level: partner_id
        col_group_results = report._compute_expression_totals_for_each_column_group(report.line_ids.expression_ids, options, groupby_to_expand="partner_id")
        if len(col_group_results) != 1:
            raise UserError(_("You can only export one period at a time with this file format!"))
        expression_list = list(col_group_results.values())
        label_dict = {exp.label: v['value'] for d in expression_list for exp, v in d.items()}
        partner_to_label_val = {}
        for label, partner_to_value_list in label_dict.items():
            for partner_id, value in partner_to_value_list:
                partner_to_label_val.setdefault(self.env['res.partner'].browse(partner_id), {})[label] = value
        return dict(sorted(partner_to_label_val.items(), key=lambda item: item[0].name))

    def check_for_error_on_partner(self, partners):
        partner_missing_information = self.env['res.partner']
        for partner in partners:
            if partner.country_id.code == "MX" and not partner.vat:
                partner_missing_information += partner
            if not partner.l10n_mx_type_of_operation:
                partner_missing_information += partner

        if partner_missing_information:
            action_error = {
                'name': _('Partner missing informations'),
                'type': 'ir.actions.act_window',
                'res_model': 'res.partner',
                'view_mode': 'list',
                'views': [(False, 'list'), (False, 'form')],
                'domain': [('id', 'in', partner_missing_information.ids)],
            }
            msg = _('The report cannot be generated because some partners are missing a valid RFC or type of operation')
            raise RedirectWarning(msg, action_error, _("See the list of partners"))

    @staticmethod
    def str_format(text):
        if not text:
            return ''
        trans_tab = {
            ord(char): None for char in (
                u'\N{COMBINING GRAVE ACCENT}',
                u'\N{COMBINING ACUTE ACCENT}',
                u'\N{COMBINING DIAERESIS}',
            )
        }
        text_n = normalize('NFKC', normalize('NFKD', text).translate(trans_tab))
        check_re = re.compile(r'''[^A-Za-z\d Ññ]''')
        return check_re.sub('', text_n)
