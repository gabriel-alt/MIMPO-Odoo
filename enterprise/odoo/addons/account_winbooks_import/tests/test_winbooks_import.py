# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import common, tagged
import base64
import requests

TESTURL = 'https://files.exact.com/static/downloads/winbooks/PARFILUX_2013.04.08.zip'
FILENAME = 'PARFILUX_2013.04.08.zip'


@tagged('post_install', '-at_install', 'external', '-standard')
class TestWinbooksImport(common.TransactionCase):

    def download_test_db(self):
        response = requests.get(TESTURL, timeout=30)
        response.raise_for_status()
        return self.env['ir.attachment'].create({
            'datas': base64.b64encode(response.content),
            'name': FILENAME,
            'mimetype': 'application/zip',
        })

    def test_winbooks_import(self):
        attachment = (
            self.env['ir.attachment'].search([('name', '=', FILENAME)])
            or self.download_test_db()
        )
        # self.env.cr.commit(); return  # uncomment to avoid fetching multiple times locally
        test_company = self.env['res.company'].create({
            'name': 'My Winbooks Company',
            'currency_id': self.env['res.currency'].search([('name', '=', 'EUR')]).id,
            'country_id': self.env.ref('base.be').id,
        })
        self.env['account.chart.template'].search([
            ('currency_id.name', '=', 'EUR'),
        ], limit=1).try_loading(test_company)
        wizard = self.env['account.winbooks.import.wizard'].with_company(test_company).create({
            'zip_file': attachment.datas,
        })
        before = self.env['account.move'].search_count([('company_id', '=', test_company.id)])
        wizard.with_company(test_company).import_winbooks_file()
        after = self.env['account.move'].search_count([('company_id', '=', test_company.id)])
        self.assertGreater(after, before)
