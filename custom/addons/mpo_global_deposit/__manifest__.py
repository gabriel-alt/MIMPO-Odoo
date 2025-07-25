# -*- coding: utf-8 -*-
{
    'name': 'Mimpo - Global Deposit',
    'version': '16.0.1.0.0',
    'summary': 'Global Deposit',
    'description': '''
      * Being able to break down a single deposit into different journal entries.
      Bank deposit Journal entry will be created, and from here
      different journal entries allocating balance will be created as well.
    ''',
    'category': 'Accounting/Accounting',
    'author': 'Port Cities LTD',
    'website': 'https://portcities.net',
    'depends': [
        'mpo_cga_generation',
        'mpo_sir_bank_reconciliation',
        'account_accountant',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/account_bank_global_deposit_views.xml',
        'views/account_bank_statement_line.xml',
	],
    'application': False,
    'installable': True,
}
