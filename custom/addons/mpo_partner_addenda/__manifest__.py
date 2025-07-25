# pylint: disable=C0111,W0104
{
    'name': 'MPO - Partner Addenda',
    'version': '16.0.2.0.0',
    'summary': "Added Addenda in XML CFDI Invoice",
    'description': """
        Added Addenda in XML CFDI Invoice
    """,
    'category': 'Accounting/Accounting',
    'author': "Port Cities Ltd",
    'website': "http://www.portcities.net",
    'depends': ['l10n_mx_edi_carta_porte', 'mpo_rater'],
    'data': ['data/4.0/cfdi.xml',
             'views/res_partner_views.xml'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
