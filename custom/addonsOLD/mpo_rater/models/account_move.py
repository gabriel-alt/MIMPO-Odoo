# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)
import psycopg2

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _rate_domain(self):
        rate_obj = self.env['base.rate'].search([])
        if len(rate_obj) > 1:
            return "['&', ('partner_ids.id', '=', partner_id), ('custom_house_ids.id', '=', house_id)]"

    rate_id = fields.Many2one(
        'base.rate', string='Tarifa', domain=_rate_domain)
    custom_house_id = fields.Many2one(
        'res.partner', string='Aduana', domain="[('is_customs_house','=',True)]")
    house_id = fields.Many2one('custom.house', string='Aduana')
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
    sir_number = fields.Char(string='Referencia', related="sir_id.number")
    pedimento = fields.Char(string='Pedimento', related="sir_id.pedimento")
    pedimento_date = fields.Char(string='Fecha pedimento', related="sir_id.pedimento_date")
    custom_house = fields.Char(string='Aduana')
    rate_currency_id = fields.Many2one(
        'res.currency', string='Divisa en tarifa')
    ship = fields.Char(string='Buque')
    supplier = fields.Char(string='Nombre de proveedor')
    total_weight = fields.Float(string='Peso')
    custom_house_ref = fields.Char(
        string='Código aduana', related="sir_id.custom_house")
    exchange_rate = fields.Float(string='Tipo de cambio')
    same_currency = fields.Boolean(string='Misma divisa?', default=True)
    rater_button = fields.Boolean(string="Activar", related="company_id.rater_button")
    is_ui_control = fields.Boolean(string="Is UI control?")
    invoice_value = fields.Float(
        string='Valor factura del pedimento',
        related="sir_id.invoice_value", readonly=False)
    total_custom_house = fields.Float(
        string='Valor aduana del pedimento',
        related="sir_id.total_custom_house", readonly=False)
    total_sale = fields.Float(
        string='Valor comercial del pedimento',
        related="sir_id.total_sale", readonly=False)
    paid_tax = fields.Float(
        string='Importe del los impuestos pagados por el cliente',
        related="sir_id.paid_tax", readonly=False)

    @api.model_create_multi
    def create(self, vals):
        """
            Here we identify the UI menu entry to show the rater functionallity.
        """
        for values in vals:
            ctx = self._context
            move_type = ctx.get('default_move_type', False)
            if move_type and move_type == 'out_invoice':
                values['is_ui_control'] = True
        return super().create(vals)

    @api.onchange('sir_id')
    def _onchange_rater_sir_id(self):
        for rec in self:
            rec.rate_id = False
            if rec.sir_id:
                # if rec.sir_id.custom_house:
                #     custom_house = self.env['res.partner'].search([('contact_number','=',rec.sir_id.custom_house)], limit=1)
                #     rec.custom_house_id = custom_house.id
                house_id = False
                if rec.sir_id.house_id:
                    house_id = rec.sir_id.house_id
                elif rec.sir_id.custom_house:
                    house_id = self.env['custom.house'].search([
                        ('number', '=', rec.sir_id.custom_house)], limit=1)
                rec.house_id = house_id and house_id.id or False
                operation = rec.sir_id.operation_type
                if str(operation) in ['1', '2']:
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
                rec.total_package = 0
                rec.total_weight = 0.00

    # @api.onchange('custom_house_ref')
    # def _onchange_custom_house_ref(self):
    #     for rec in self:
    #         if rec.custom_house_ref:
    #             # partner = self.env['res.partner'].search(
    #             #     [('contact_number', '=', rec.custom_house_ref)], limit=1)
    #             # rec.custom_house_id = partner.id
    #             house = self.env['custom.house'].search(
    #                 [('number', '=', rec.custom_house_ref)], limit=1)
    #             rec.house_id = house.id

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
                amount_rate_1 = amount_rate_1 * self.exchange_rate
                if container_qty > 0.00:
                    amount_rate_1 = amount_rate_1 * container_qty
            else:
                amount_rate_1 = amount_rate_1 / self.exchange_rate
                if container_qty > 0.00:
                    amount_rate_1 = amount_rate_1 * container_qty
            return amount_rate_1, False

    def rate_compute(self):
        _logger.info("*"*50)
        _logger.info("Starting Tarificador computation for Sale Order %s", )
        inv_id = self._context.get('inv_id', False)
        if inv_id:
            inv_obj = self.env['account.move'].browse(inv_id)
            type_service = inv_obj.operation_type
            result = inv_obj.rate_id.compute_rate(type_service, inv_obj)
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
                product_coincidence = self.invoice_line_ids.filtered(lambda item: item.product_id.id == product_id_1.id)
                if product_coincidence:
                    product_coincidence.price_unit = currency_amount
                else:
                    move_line_vals = {
                        'product_id': product_id_1.id,
                        'move_id': self.id,
                        'price_unit': currency_amount,
                        'analytic_distribution': {
                            self.sir_id.account_analytic_id.id: 100
                        }
                    }
                    self.invoice_line_ids.create(move_line_vals)
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
                product_coincidence = self.invoice_line_ids.filtered(lambda item: item.product_id.id == product_id_2.id)
                if product_coincidence:
                    product_coincidence.price_unit = currency_amount
                else:
                    move_line_vals = {
                        'product_id': product_id_2.id,
                        'move_id': self.id,
                        'price_unit': currency_amount,
                        'analytic_distribution': {
                            self.sir_id.account_analytic_id.id: 100
                        }
                    }
                    self.invoice_line_ids.create(move_line_vals)
            if product_id_3:
                for product in product_id_3:
                    if product.amount <= 0.00:
                        raise UserError(_("El importe en tarifa para *Otros conceptos* es: %s", str(product.amount)))
                    currency_amount, ignored = self.validate_currency(product.currency_id, product.amount)
                    product_coincidence = self.invoice_line_ids.filtered(lambda item: item.product_id.id == product.product_id.id)
                    if product_coincidence:
                        product_coincidence.price_unit = currency_amount
                    else:
                        move_line_vals = {
                            'product_id': product.product_id.id,
                            'move_id': self.id,
                            'price_unit': currency_amount,
                            'analytic_distribution': {
                                self.sir_id.account_analytic_id.id: 100
                            }
                        }
                        self.invoice_line_ids.create(move_line_vals)