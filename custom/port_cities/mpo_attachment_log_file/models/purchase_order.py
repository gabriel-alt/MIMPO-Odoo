""" Purchase Order """
from odoo import models, fields


class PurchaseOrderLine(models.Model):
    """ Inherit Purchase Order Line """
    _inherit = 'purchase.order.line'

    related_attachment_id = fields.Many2one(
        'ir.attachment', domain="[('res_model', '=', 'purchase.order')]")
