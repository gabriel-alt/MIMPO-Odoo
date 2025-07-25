""" Product Template """
from odoo import models, fields


class ProductTemplate(models.Model):
    """ Inherit Product Template """
    _inherit = 'product.template'

    notif_quote_template_id = fields.Many2one(
        'mail.template', string='Notif Quote Template',
        domain="[('model', '=', 'purchase.order')]")
