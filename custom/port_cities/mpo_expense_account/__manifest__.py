# -*- coding: utf-8 -*-
##############################################################################
#                 @author Port Cities LTD
#
##############################################################################

{
    'name': 'MIMPO - Expense Account',
    'version': '16.0.1.0.1',
    'description': ''' 
        Custom to add 3rd party account in vendor bill
    ''',
    'category': 'Accounting',
    'author': 'Port Cities LTD',
    'website': 'www.portcities.net',
    'depends': [
        'account_accountant',
        'mpo_sir'
    ],
    'data': [
        'views/partner_views.xml',
        'views/product_template_view.xml',
        'views/account_move_view.xml',
        'views/purchase_order_view.xml'
    ],
    'application': False,
    'installable': True,
}
