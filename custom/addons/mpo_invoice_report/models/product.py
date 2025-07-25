""" Product Template """
from odoo import models, fields


class ProductTemplate(models.Model):
    """ Inherit Product Template """
    _inherit = 'product.template'

    show_sale_description = fields.Boolean(string='Visible en factura PDF?')
