""" Config Settings """
from odoo import models, fields

class Company(models.Model):
    """ Inherit Company """
    _inherit = "res.company"

    global_deposit_journal_id = fields.Many2one(
        'account.journal', string='Global Deposit Journal',
        domain="[('type', 'in', ['general'])]")


class ConfigSettings(models.TransientModel):
    """ Inherit Config Settings """
    _inherit = "res.config.settings"

    global_deposit_journal_id = fields.Many2one(
        'account.journal', string='Global Deposit Journal',
        related='company_id.global_deposit_journal_id', readonly=False,
        domain="[('company_id', '=', company_id), ('type', 'in', ['general'])]")
