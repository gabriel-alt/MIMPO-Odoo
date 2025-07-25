# -*- coding: utf-8 -*-
##############################################################################
#                 @author Port Cities LTD
#
##############################################################################

{
    'name': 'Tarificador',
    'version': '16.0.1',
    'description': ''' 
      * Allows to set and extra amount in product lines, this apply to sale order and sale invoice.
    ''',
    'category': 'Uncategorize',
    'author': 'Port Cities LTD',
    'website': 'www.portcities.net',
    'depends': [
        'base',
        'sale',
        'account',
        'mpo_sir',
        'mpo_contact_type'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/reports/report_saleorder_document.xml',
        'views/base_rate.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/account_move.xml',
        'views/res_config_settings_view.xml',
    ],
    'application': False,
    'installable': True,
}
