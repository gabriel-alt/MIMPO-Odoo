# pylint: disable=C0111,W0104
{
    'name': 'CGA Report',
    'version': '16.0.2.0.0',
    'summary': "Generate CGA Invoice Report",
    'description': """
        Generate CGA Invoice Report
    """,
    'category': 'Accounting/Accounting',
    'author': "Port Cities Ltd",
    'website': "http://www.portcities.net",
    'depends': ['mpo_cga_generation',
                'mpo_invoice_report'],
    'data': ['report/cga_reports.xml',
             'report/ms_cga_reports.xml',
             'views/account_move_view.xml'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
