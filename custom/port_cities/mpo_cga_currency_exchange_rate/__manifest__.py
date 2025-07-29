# -*- coding: utf-8 -*-
##############################################################################
#                 @author Port Cities LTD
#
##############################################################################

{
    'name': 'CGA Generation Currency Exchange Rate',
    'version': '16.0.1.0.0',
    'description': '''
      * Update some CGA Generation based on manual exchange rate.
    ''',
    'category': 'Accounting/Accounting',
    'author': 'Port Cities LTD',
    'website': 'https://portcities.net',
    'depends': [
        'mpo_cga_generation', 'bi_manual_currency_exchange_rate'
    ],
    'data': [
	],
    'application': False,
    'installable': True,
}
