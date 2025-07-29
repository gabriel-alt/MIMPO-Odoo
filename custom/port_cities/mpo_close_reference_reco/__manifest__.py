# -*- coding: utf-8 -*-
##############################################################################
#                 @author Port Cities LTD
#
##############################################################################

{
    'name': 'Partner Sync with RECO',
    'version': '16.0.1',
    'description': '''
      * Allows to update new records from odoo to SIR.
    ''',
    'category': 'Uncategorize',
    'author': 'Port Cities LTD',
    'website': 'https://portcities.net',
    'depends': [
        'mpo_sir'
    ],
    'data': [
        # 'security/ir.model.access.csv',
	],
    'application': False,
    'installable': True,
}
