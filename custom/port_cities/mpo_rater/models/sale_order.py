# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _rate_domain(self):
        return ""
        # rate_obj = self.env['base.rate'].search([])
        # if len(rate_obj) > 1:
        #     return "['&', ('partner_ids.id', '=', partner_id), ('custom_house_ids.id', '=', house_id)]"

    rate_id = fields.Many2one(
        'base.rate', string='Tarifa', domain=_rate_domain)
    custom_house_id = fields.Many2one(
        'res.partner', string='Aduana', domain="[('is_customs_house','=',True)]")
    house_id = fields.Many2one('custom.house', string='Aduana')
    # custom_house_id = fields.Many2one(
    #     'res.partner', string='Aduana', domain="[('x_studio_many2one_field_Uug31.x_name','=','Aduana')]")
    operation_type = fields.Selection(
        selection=[('1', 'Importación'),
                   ('2', 'Exportación')],
        string='Tipo de servicio')
    ware = fields.Char(string='Mercancía')
    pedimento_invoice = fields.Char(string='Facturas')
    number_mark = fields.Char(string='Marcas y números')
    total_package = fields.Integer(string='Cantidad de bultos')
    reception = fields.Char(string='Recepción')
    order_number = fields.Char(string='N° Pedido')
    ref_document = fields.Char(string='Clave documento')
    sir_number = fields.Char(string='Referencia', related="sir_id.number")
    pedimento = fields.Char(string='Pedimento', related="sir_id.pedimento")
    pedimento_date = fields.Char(string='Fecha pedimento', related="sir_id.pedimento_date")
    custom_house = fields.Char(string='Aduana')
    rate_currency_id = fields.Many2one(
        'res.currency', string='Divisa en tarifa')
    ship = fields.Char(string='Buque')
    supplier = fields.Char(string='Nombre de proveedor')
    total_weight = fields.Float(string='Peso')
    # catalog_id = fields.Char(string='Selección de un catálogo')
    custom_house_ref = fields.Char(
        string='Código aduana', related="sir_id.custom_house")
    exchange_rate = fields.Float(string='Tipo de cambio')
    same_currency = fields.Boolean(string='Misma divisa?', default=True)
    total_taxes = fields.Float(string='Total impuestos')
    amount_dta = fields.Float(string='DTA')
    amount_adv = fields.Float(string='ADV')
    amount_ieps = fields.Float(string='IEPS')
    amount_other = fields.Float(string='Otros')
    amount_iva = fields.Float(string='IVA')
    amount_insurance = fields.Float(string='Seguro')
    amount_expense = fields.Float(string='Bills')
    amount_ded_other = fields.Float(string='Otros')
    total_inc = fields.Float(string='Incrementables')
    rater_button = fields.Boolean(string="Activar", related="company_id.rater_button")

    @api.onchange('partner_id')
    def _onchange_partner_id_warning(self):
        super()._onchange_partner_id_warning()
        if self.partner_id:
            rate_ids = self.env['base.rate'].search(
                [('partner_ids', 'in', self.partner_id.id)])
            if rate_ids:
                self.rate_id = rate_ids[0]

    @api.onchange('sir_id')
    def _onchange_rater_sir_id(self):
        for rec in self:
            # rec.rate_id = False
            if rec.sir_id:
                # if rec.sir_id.custom_house:
                #     custom_house = self.env['res.partner'].search([('contact_number','=',rec.sir_id.custom_house)], limit=1)
                #     rec.custom_house_id = custom_house.id
                operation = rec.sir_id.operation_type
                rec.operation_type = str(operation)
                rec.pedimento_invoice = rec.sir_id.pedimento_invoice
                rec.number_mark = rec.sir_id.pedimento_invoice
                rec.ware = rec.sir_id.ware
                rec.total_package = rec.sir_id.total_package
                rec.reception = rec.sir_id.reception
                rec.order_number = rec.sir_id.order_number
                rec.custom_house = rec.sir_id.custom_house
                rec.ship = rec.sir_id.ship
                rec.supplier = rec.sir_id.supplier
                rec.total_weight = rec.sir_id.total_weight
                rec.ref_document = rec.sir_id.ref_document
                rec.total_taxes = rec.sir_id.total_taxes
                rec.amount_dta = rec.sir_id.amount_dta
                rec.amount_adv = rec.sir_id.amount_adv
                rec.amount_ieps = rec.sir_id.amount_ieps
                rec.amount_other = rec.sir_id.amount_other
                rec.amount_iva = rec.sir_id.amount_iva
                rec.amount_insurance = rec.sir_id.amount_insurance
                rec.amount_expense = rec.sir_id.amount_expense
                rec.amount_ded_other = rec.sir_id.amount_ded_other
                rec.total_inc = rec.sir_id.total_inc
            else:
                rec.custom_house_id = False
                rec.operation_type = False
                rec.pedimento_invoice = ''
                rec.number_mark = ''
                rec.ware = ''
                rec.reception = ''
                rec.order_number = ''
                rec.custom_house = ''
                rec.ship = ''
                rec.supplier = ''
                rec.ref_document = ''
                rec.total_package = 0
                rec.total_weight = 0.00
                rec.total_taxes = 0.00
                rec.amount_dta = 0.00
                rec.amount_adv = 0.00
                rec.amount_ieps = 0.00
                rec.amount_other = 0.00
                rec.amount_iva = 0.00
                rec.amount_insurance = 0.00
                rec.amount_expense = 0.00
                rec.amount_ded_other = 0.00
                rec.total_inc = 0.00

    @api.onchange('custom_house_ref')
    def _onchange_custom_house_ref(self):
        for rec in self:
            if rec.custom_house_ref:
                partner = self.env['res.partner'].search(
                    [('contact_number', '=', rec.custom_house_ref)], limit=1)
                rec.custom_house_id = partner.id

    @api.onchange('rate_id')
    def _onchange_rate_id(self):
        for rec in self:
            if rec.rate_id and rec.operation_type == '1':
                ignored, rec.same_currency = self.validate_currency(rec.rate_id.in_currency_id_1)
                if rec.same_currency:
                    ignored, rec.same_currency = self.validate_currency(rec.rate_id.in_currency_id_2)
                if rec.same_currency:
                    for item in rec.rate_id.other_rate_ids:
                        ignored, rec.same_currency = self.validate_currency(item.currency_id)
            elif rec.rate_id and rec.operation_type == '2':
                ignored, rec.same_currency = self.validate_currency(rec.rate_id.out_currency_id_1)
                if rec.same_currency:
                    ignored, rec.same_currency = self.validate_currency(rec.rate_id.out_currency_id_2)
                if rec.same_currency:
                    for item in rec.rate_id.other_rate_ids:
                        ignored, rec.same_currency = self.validate_currency(item.currency_id)

    def validate_currency(self, currency_id_1, amount_rate_1=0.00, container_qty=0.00):
        if self.currency_id.id == currency_id_1.id:
            if container_qty > 0.00:
                amount_rate_1 = amount_rate_1 * container_qty
            return amount_rate_1, True
        else:
            if self.currency_id.id == self.env.ref('base.MXN').id:
                amount_rate_1 = amount_rate_1 * (self.exchange_rate or 1.00)
                if container_qty > 0.00:
                    amount_rate_1 = amount_rate_1 * container_qty
            else:
                amount_rate_1 = amount_rate_1 / (self.exchange_rate or 1.00)
                if container_qty > 0.00:
                    amount_rate_1 = amount_rate_1 * container_qty
            return amount_rate_1, False

    def rate_compute(self):
        _logger.info("*"*50)
        _logger.info("Starting Tarificador computation for Sale Order %s", )
        sale_id = self._context.get('sale_id', False)
        if sale_id:
            sale_obj = self.env['sale.order'].browse(sale_id)
            type_service = sale_obj.operation_type
            result = sale_obj.rate_id.compute_rate(type_service, sale_obj)
            print(result)
            product_id_1 = result.get('product_id', False)
            amount_rate_1 = result.get('amount_rate', False)
            currency_id_1 = result.get('currency_id', False)
            product_id_2 = result.get('product_id_2', False)
            amount_rate_2 = result.get('amount_rate_2', False)
            currency_id_2 = result.get('currency_id_2', False)
            product_id_3 = result.get('product_id_3', False)
            container_amount = result.get('container_amount', False)
            container_amount_2 = result.get('container_amount_2', False)
            container_qty = self.sir_id.container_qty if container_amount else 0.00
            container_qty_2 = self.sir_id.container_qty if container_amount_2 else 0.00
            if product_id_1:
                currency_amount, ignored = self.validate_currency(currency_id_1, amount_rate_1) if not container_amount else self.validate_currency(currency_id_1, container_amount, container_qty)
                compare_min_max = currency_amount
                if self.operation_type == '1':
                    if compare_min_max < self.rate_id.in_min_amount_1 and self.rate_id.in_min_amount_1 != 0.00:
                        currency_amount = self.rate_id.in_min_amount_1
                    if compare_min_max > self.rate_id.in_max_amount_1 and self.rate_id.in_max_amount_1 != 0.00:
                        currency_amount = self.rate_id.in_max_amount_1
                else:
                    if compare_min_max < self.rate_id.out_min_amount_1 and self.rate_id.out_min_amount_1 != 0.00:
                        currency_amount = self.rate_id.out_min_amount_1
                    if compare_min_max > self.rate_id.out_max_amount_1 and self.rate_id.out_max_amount_1 != 0.00:
                        currency_amount = self.rate_id.out_max_amount_1
                product_coincidence = self.order_line.filtered(lambda item: item.product_id.id == product_id_1.id)
                if product_coincidence:
                    product_coincidence.price_unit = currency_amount
                else:
                    order_line_vals = {
                        'product_id': product_id_1.id,
                        'order_id': self.id,
                        'price_unit': currency_amount,
                    }
                    self.order_line.create(order_line_vals)
            if product_id_2:
                currency_amount, ignored = self.validate_currency(currency_id_2, amount_rate_2) if not container_amount_2 else self.validate_currency(currency_id_2, container_amount_2, container_qty_2)
                compare_min_max = currency_amount
                if self.operation_type == '1':
                    if compare_min_max < self.rate_id.in_min_amount_2 and self.rate_id.in_min_amount_2 != 0.00:
                        currency_amount = self.rate_id.in_min_amount_2
                    if compare_min_max > self.rate_id.in_max_amount_2 and self.rate_id.in_max_amount_2 != 0.00:
                        currency_amount = self.rate_id.in_max_amount_2
                else:
                    if compare_min_max < self.rate_id.out_min_amount_2 and self.rate_id.out_min_amount_2 != 0.00:
                        currency_amount = self.rate_id.out_min_amount_2
                    if compare_min_max > self.rate_id.out_max_amount_2 and self.rate_id.out_max_amount_2 != 0.00:
                        currency_amount = self.rate_id.out_max_amount_2
                product_coincidence = self.order_line.filtered(lambda item: item.product_id.id == product_id_2.id)
                if product_coincidence:
                    product_coincidence.price_unit = currency_amount
                else:
                    order_line_vals = {
                        'product_id': product_id_2.id,
                        'order_id': self.id,
                        'price_unit': currency_amount,
                    }
                    self.order_line.create(order_line_vals)
            if product_id_3:
                for product in product_id_3:
                    if product.amount <= 0.00:
                        raise UserError(_("El importe en tarifa para *Otros conceptos* es: %s", str(product.amount)))
                    currency_amount, ignored = self.validate_currency(product.currency_id, product.amount)
                    product_coincidence = self.order_line.filtered(lambda item: item.product_id.id == product.product_id.id)
                    if product_coincidence:
                        product_coincidence.price_unit = currency_amount
                    else:
                        order_line_vals = {
                            'product_id': product.product_id.id,
                            'order_id': self.id,
                            'price_unit': currency_amount,
                        }
                        self.order_line.create(order_line_vals)

