# pylint: disable=C0111,W0104
{
    'name': 'Contact Type',
    'version': '16.0.1.0.0',
    'summary': "Identify Contact Type of a Partner",
    'description': """
        Define Partner's Contact Type and Link it to the Transaction Data
    """,
    'category': 'Sales/CRM',
    'author': "Port Cities Ltd",
    'website': "http://www.portcities.net",
    'depends': ['contacts',
                'sale_management',
                'purchase'],
    'data': ['security/ir.model.access.csv',
             'data/contact_type_data.xml',
             'views/custom_house_view.xml',
             'views/account_move_view.xml',
             'views/purchase_order_view.xml',
             'views/sale_order_view.xml',
             'views/partner_view.xml'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
