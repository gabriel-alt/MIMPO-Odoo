""" Config Settings """
from odoo import models, fields

class ConfigSettings(models.TransientModel):
    """ Inherit Config Settings """

    _inherit = "res.config.settings"

    sir_analytic_plan_id = fields.Many2one(
        'account.analytic.plan', related="company_id.sir_analytic_plan_id",
        readonly=False, string='Default SIR Analytic Plan',
        help="Default analytic plan of analytic account created from SIR Reference creation")
