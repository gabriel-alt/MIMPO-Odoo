##############################################################################
#                 @author Port Cities LTD
#
##############################################################################

{
    'name': 'MIMPO - Notification Creating a Quote Request',
    'version': '16.0.1.0.1',
    'description': ''' 
        Generate notification when creating a quote request in the purchasing module
    ''',
    'category': 'Purchase',
    'author': 'Port Cities LTD',
    'website': 'www.portcities.net',
    'depends': [
        'purchase',
    ],
    'data': [
        'data/mail_template_data.xml',
        'views/product_view.xml'
    ],
    'application': False,
    'installable': True,
}
