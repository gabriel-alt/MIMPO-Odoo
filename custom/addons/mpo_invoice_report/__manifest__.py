# -*- coding: utf-8 -*-
##############################################################################
#                 @author Port Cities LTD
#
##############################################################################

{
    'name': 'MIMPO - Invoice Report',
    'version': '16.0.2.0.0',
    'description': ''' 
        Custom invoice report
    ''',
    'category': 'Reporting',
    'author': 'Port Cities LTD',
    'website': 'www.portcities.net',
    'depends': ['l10n_mx_edi',
                'mpo_sir', 'mpo_partner_reco'],
    'data': [
        'views/account_tax_views.xml',
        'views/product_view.xml',
        'reports/report_account_move.xml'],
    'application': False,
    'installable': True,
}
