# -*- coding: utf-8 -*-
{
    'name': 'Mimpo - Disable automatic invoicing (stamp)',
    'version': '16.0.1.0.0',
    'summary': "Disable automatic invoicing (stamp) on invoices",
    'description': '''
      * Disable automatic invoicing (stamp) on invoices.
    ''',
    'category': 'Accounting/Accounting',
    'author': "Port Cities Ltd",
    'website': "http://www.portcities.net",
    'depends': [
        'mpo_sir',
        'l10n_mx_edi_extended_40',
    ],
    'data': [
        'views/account_move_views.xml',
	],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
