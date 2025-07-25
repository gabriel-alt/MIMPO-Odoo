##############################################################################
#                 @author Port Cities LTD
##############################################################################

{
    'name': 'MPO - Down Payment Credit Note',
    'version': '16.0.1.0.0',
    'description': '''
      * Down Payment Credit Note.
    ''',
    'category': 'Accounting/Accounting',
    'author': 'Port Cities LTD',
    'website': 'https://portcities.net',
    'depends': [
        'mpo_sir', 'l10n_mx_edi'
    ],
    'data': [
        'views/partner_views.xml',
        'views/account_journal_views.xml',
        'views/account_move_views.xml',
	],
    'application': False,
    'installable': True,
}
