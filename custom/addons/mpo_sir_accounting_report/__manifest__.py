##############################################################################
#                 @author Port Cities LTD
#
##############################################################################

{
    'name': 'MIMPO - SIR Accounting Reports',
    'version': '16.0.1.0.1',
    'description': ''' 
        Accounting Reports adding SIR
    ''',
    'category': 'Accounting/Accounting',
    'author': 'Port Cities LTD',
    'website': 'www.portcities.net',
    'depends': [
        'account_reports', 'mpo_sir_accounting'
    ],
    'data': [
        'data/aged_partner_balance.xml',
        'data/general_ledger.xml',
    ],
    'application': False,
    'installable': True,
}
