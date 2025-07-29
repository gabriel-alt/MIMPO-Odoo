# -*- coding: utf-8 -*-
##############################################################################
#                 @author Port Cities LTD
#
##############################################################################

{
    "name": "SIR System Integration",
    "version": "16.0.1",
    "description": """
      * Allows to create new records from SIR.
    """,
    "category": "Uncategorize",
    "author": "Port Cities LTD",
    "website": "www.portcities.net",
    "depends": [
        "sale_management",
        "purchase",
        "pci_api",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/sir_reference.xml",
        "views/res_partner.xml",
        "views/sale_order.xml",
        "views/account_move.xml",
        # 'views/account_payment_views.xml',
        "views/purchase_order.xml",
        "views/res_config_settings_view.xml",
    ],
    "application": False,
    "installable": True,
}
