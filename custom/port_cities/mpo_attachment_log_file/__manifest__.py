##############################################################################
#                 @author Port Cities LTD
#
##############################################################################

{
    'name': 'MIMPO - Attachments related to log line',
    'version': '16.0.1.0.1',
    'description': ''' 
        Attachments related to log line
    ''',
    'category': 'Attachments',
    'author': 'Port Cities LTD',
    'website': 'www.portcities.net',
    'depends': [
        'purchase',
    ],
    'data': [
        'views/account_move_view.xml',
        'views/purchase_order_view.xml'
    ],
    'application': False,
    'installable': True,
}
