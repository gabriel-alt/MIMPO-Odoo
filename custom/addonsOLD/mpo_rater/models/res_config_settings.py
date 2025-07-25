""" Config Settings """
from odoo import models, fields

class Company(models.Model):
    _inherit = "res.company"

    rater_button = fields.Boolean(string="Activar")

class ConfigSettings(models.TransientModel):
    """ Inherit Config Settings """

    _inherit = "res.config.settings"

    rater_button = fields.Boolean(string="Activar", related='company_id.rater_button', readonly=False)
