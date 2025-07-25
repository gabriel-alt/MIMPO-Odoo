# -*- coding: utf-8 -*-
##############################################################################
#                 @author Port Cities LTD
#
##############################################################################

{
    'name': 'SIR Accounting',
    'version': '16.0.1.0.0',
    'description': '''
      * Set SIR on Invoice/Bill based on SIR set on SO.
    ''',
    'category': 'Accounting/Accounting',
    'author': 'Port Cities LTD',
    'website': 'www.portcities.net',
    'depends': [
        'account_accountant',
        'mpo_sir',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'wizard/change_reference_sir_wizard_views.xml',
        'wizard/account_payment_register_views.xml',
	],
    'application': False,
    'installable': True,
}
