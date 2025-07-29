{
    "name": "MPO - Intercompany Invoices Company",
    "version": "16.0.2.0.0",
    "author": "Port Cities",
    "website": "https://www.portcities.net",
    "sequence": 1,
    "category": "Accounting/Accounting",
    "summary": "Intercompany Invoices Company",
    "depends": [
        "account_inter_company_rules",
        "sale_purchase_inter_company_rules",
        "mpo_sir_accounting", "mpo_rater"],
    "data": [
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "AGPL-3",
}
