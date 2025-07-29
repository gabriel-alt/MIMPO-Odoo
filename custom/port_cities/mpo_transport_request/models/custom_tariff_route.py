# -*- coding: utf-8 -*-

from odoo import models, fields, api, http
from odoo.exceptions import ValidationError, UserError

class CustomerTariffRoute(models.Model):
    _name = 'custom.tariff.route'
    _descripcion = 'Customer Tariff Route'
    
    name = fields.Char(
        compute="_compute_tarif_route_name",
        required=True, store=True, index=True, readonly=False)
    origin_id = fields.Many2one('res.city')
    destiny_id = fields.Many2one('res.city')
    unit_type_id = fields.Many2one('unit.type', string='Unit Type')
    active = fields.Boolean(string='Activo', default=True)

    @api.depends('origin_id', 'destiny_id', 'unit_type_id')
    def _compute_tarif_route_name(self):
        for this in self:
            name = ''
            if this.unit_type_id:
                name = '[' + this.unit_type_id.name + '] '
            if this.origin_id:
                name += this.origin_id.name
            if this.destiny_id:
                if this.origin_id:
                    name += ' → '
                name += this.destiny_id.name
            this.name = name or 'Tarif Route'
