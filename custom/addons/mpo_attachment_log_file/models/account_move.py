""" Account Move """
from odoo import models, fields


class AccountMoveLine(models.Model):
    """ Inherit Account Move Line """
    _inherit = 'account.move.line'

    related_attachment_id = fields.Many2one(
        'ir.attachment', domain="[('res_model', '=', 'account.move')]")
