# pylint: disable=C0111,W0104
{
    'name': 'CGA Generation',
    'version': '16.0.2.0.0',
    'summary': "Linking Expense to the Related Invoice",
    'description': """
        Linking Expense to the Related Invoice
    """,
    'category': 'Accounting/Accounting',
    'author': "Port Cities Ltd",
    'website': "http://www.portcities.net",
    'depends': ['l10n_mx_edi_extended_40',
                'account_edi_ubl_cii',
                'account_accountant',
                'mpo_sir',
                'mpo_expense_account',
                'mpo_down_payment_credit_note',
                'l10n_mx_edi_carta_porte'],
    'data': ['data/4.0/cfdi.xml',
             'views/account_account_view.xml',
             'views/partner_views.xml',
             'views/account_move_view.xml'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
