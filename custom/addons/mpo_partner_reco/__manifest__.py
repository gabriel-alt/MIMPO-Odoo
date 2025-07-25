# -*- coding: utf-8 -*-
##############################################################################
#                 @author Port Cities LTD
#
##############################################################################

{
    'name': 'Partner Sync with RECO',
    'version': '16.0.1',
    'description': '''
      * Allows to create new records from odoo to SIR.
    ''',
    'category': 'Uncategorize',
    'author': 'Port Cities LTD',
    'website': 'https://portcities.net',
    'depends': [
        'base',
        'l10n_mx_edi_extended',
        'l10n_mx_edi_carta_porte',
        'l10n_mx_edi_extended_40'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
	],
    'application': False,
    'installable': True,
}
