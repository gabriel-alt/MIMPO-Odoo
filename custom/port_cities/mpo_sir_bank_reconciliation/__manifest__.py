# -*- coding: utf-8 -*-
##############################################################################
#                 @author Port Cities LTD
#
##############################################################################

{
    'name': 'SIR Bank Reconciliation',
    'version': '16.0.1.0.0',
    'description': '''
      * Set SIR on Bank Statement Line.
    ''',
    'category': 'Accounting/Accounting',
    'author': 'Port Cities LTD',
    'website': 'www.portcities.net',
    'depends': [
        'account_accountant',
        'mpo_sir',
    ],
    'data': [
        'views/account_bank_statement_line.xml',
	],
    'application': False,
    'installable': True,
}
