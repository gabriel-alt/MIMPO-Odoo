""" Account Move """
from odoo import models, fields

class AccountTax(models.Model):
    """ Inherit Account Tax """
    _inherit = 'account.tax'

    impuesto_tax_code = fields.Char(string="Tax Code")
    impuesto_tax_name = fields.Char(string="Tax Name")
