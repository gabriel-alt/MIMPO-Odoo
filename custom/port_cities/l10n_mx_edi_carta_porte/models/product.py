# -*- coding: utf-8 -*-
from odoo import fields, models, api,_

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    clave_stcc = fields.Char(string='Clave STCC')
    dimensiones = fields.Char(string='Dimensiones XX/XX/XXcm')
    materialpeligroso = fields.Selection(
        selection=[('Sí', 'Si'),
                   ('No', 'No'),],
        string=_('Material peligroso'),
    )
    embalaje = fields.Many2one('cve.tipo.embalaje', string='Embalaje')
    desc_embalaje = fields.Char(string='Descripción de embalaje')
    clavematpeligroso = fields.Many2one('cve.material.peligroso',string='Clave material peligroso')
