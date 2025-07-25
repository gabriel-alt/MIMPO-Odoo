# -*- coding: utf-8 -*-

from odoo import models, fields, api, http
from odoo.exceptions import ValidationError, UserError

class CustomerRateService(models.Model):
    _name = 'customer.rate.service'
    _descripcion = 'Customer Rate Service'
    
    name = fields.Char(
        required=True, index=True, string="Description", translate=True)
    partner_ids = fields.Many2many(
        "res.partner", "customer_rate_service_partner_rel",
        string="Customers")
    # start_date = fields.Date('Validity Start Date')
    # end_date = fields.Date('Validity Start Date')
    user_id = fields.Many2one(
        'res.users', string='Responsible',
        default=lambda self: self.env.user)
    tarif_element_ids = fields.One2many(
        'customer.rate.tarif.element', 'rate_id', string='Tarif Elements')

class CustomerRateTarifElement(models.Model):
    _name = 'customer.rate.tarif.element'
    _descripcion = 'Customer Rate Tarif Element'

    rate_id = fields.Many2one(
        'customer.rate.service', string='Customer Rate', 
        index=True, required=True, ondelete='cascade')
    solo_transporte = fields.Boolean(compute="_compute_company_solo_transporte")
    freight = fields.Boolean()
    route_id = fields.Many2one('custom.tariff.route')
    product_id = fields.Many2one(
        'product.product', string='Product',
        change_default=True, index='btree_not_null')
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product Template',
        related='product_id.product_tmpl_id', store=True)
    name = fields.Char(
        compute="_compute_tarif_name",
        required=True, store=True, readonly=False)
    origin_id = fields.Many2one('res.city')
    destiny_id = fields.Many2one('res.city')
    unit_type_id = fields.Many2one('unit.type', string='Unit Type')
    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True,
        default=lambda self: self.env.company.currency_id.id)
    customer_price = fields.Monetary()
    related_fee = fields.Monetary()
    vendor_cost_ids = fields.Many2many(
        'product.supplierinfo', string='Vendors Costs',
        domain="['|', ('product_id', '=', product_id), ('product_tmpl_id', '=', product_tmpl_id)]")

    @api.depends('product_id', 'route_id', 'freight')
    def _compute_tarif_name(self):
        for this in self:
            name = ''
            if this.product_id:
                name = this.product_id.display_name
            if this.route_id and this.freight:
                if name:
                    name += ' - '
                name += this.route_id.name
            this.name = name or 'Rate Tarif Element'

    def _compute_company_solo_transporte(self):
        solo_transporte = self.env.company.solo_transporte
        for this in self:
            this.solo_transporte = solo_transporte
