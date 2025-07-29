from odoo import fields, models


class ResPartner(models.Model):
    """inherit res.partner"""
    _inherit = "res.partner"

    gain_margin = fields.Float(string="Profit Margin")

class ResCompany(models.Model):
    """inherit res.company"""
    _inherit = "res.company"

    solo_transporte = fields.Boolean(string="Solo transporte")
