# -*- coding: utf-8 -*-
""" Company """
from odoo import models, fields

class ResCompany(models.Model):
    """ Inherit Company """

    _inherit = 'res.company'

    sir_analytic_plan_id = fields.Many2one(
        'account.analytic.plan', string='Default SIR Analytic Plan')
