# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BaseRate(models.Model):
    _name = 'base.rate'
    _rec_name = "name"

    def _set_domain(self):
        sir_ref_id = self.env.ref('mpo_sir.model_sir_ref').id
        by_model = ('model_id', '=', sir_ref_id)
        by_field_type = ('ttype', 'in', ['float', 'integer'])
        return ['&', by_model, by_field_type]

    name = fields.Char(string='Nombre tarifa')
    start_date = fields.Date(string='Fecha inicial')
    end_date = fields.Date(string='Fecha final')
    partner_ids = fields.Many2many(
        'res.partner', 'res_partner_base_rate_rel', 'rate_id', 'partner_id', string='Clientes')
    partner_customs_ids = fields.Many2many(
        'res.partner', 'res_partner_custom_base_rate_rel', 'rate_id', 'partner_id', string='Aduanas', domain="[('is_customs_house','=',True)]")
    custom_house_ids = fields.Many2many(
        'custom.house', 'custom_house_base_rate_rel',
        'rate_id', 'custom_house_id', string='Aduanas')
    # partner_customs_ids = fields.Many2many(
    #     'res.partner', 'res_partner_custom_base_rate_rel', 'rate_id', 'partner_id', string='Aduanas', domain="[('x_studio_many2one_field_Uug31.x_name','=','Aduana')]")
    in_product_id_1 = fields.Many2one(
        'product.product', string="Producto en factura")
    in_apply_on_1 = fields.Selection(
        selection=[('percentage', 'Porcentaje'),
                   ('fixed', 'Cuota fija'),
                   ('container', 'Contenedor')],
        string='Aplica por')
    in_currency_id_1 = fields.Many2one(
        'res.currency', string="Divisa")
    in_percentage_amount_1 = fields.Float(string='Porcentaje')
    in_is_expense_1 = fields.Boolean(string='Calcular gastos?')
    in_min_amount_1 = fields.Float(string='Monto mínimo')
    in_max_amount_1 = fields.Float(string='Monto máximo')
    in_field_ids_1 = fields.Many2many(
        'ir.model.fields', 'in_ir_model_fields_base_rate_rel', 'rate_id', 'field_id', string='Campos', domain=_set_domain)
    in_fixed_amount_1 = fields.Float(string='Cuota fija')
    in_container_amount_1 = fields.Float(string='Importe por contenedor')
    out_product_id_1 = fields.Many2one(
        'product.product', string="Producto en factura")
    out_apply_on_1 = fields.Selection(
        selection=[('percentage', 'Porcentaje'),
                   ('fixed', 'Cuota fija'),
                   ('container', 'Contenedor')],
        string='Aplica por')
    out_currency_id_1 = fields.Many2one(
        'res.currency', string="Divisa")
    out_percentage_amount_1 = fields.Float(string='Porcentaje')
    out_is_expense_1 = fields.Boolean(string='Calcular gastos?')
    out_min_amount_1 = fields.Float(string='Monto mínimo')
    out_max_amount_1 = fields.Float(string='Monto máximo')
    out_field_ids_1 = fields.Many2many(
        'ir.model.fields', 'out_ir_model_fields_base_rate_rel', 'rate_id', 'field_id', string='Campos', domain=_set_domain)
    out_fixed_amount_1 = fields.Float(string='Cuota fija')
    out_container_amount_1 = fields.Float(string='Importe por contenedor')

    in_product_id_2 = fields.Many2one(
        'product.product', string="Producto en factura")
    in_apply_on_2 = fields.Selection(
        selection=[('percentage', 'Porcentaje'),
                   ('fixed', 'Cuota fija'),
                   ('container', 'Contenedor')],
        string='Aplica por')
    in_currency_id_2 = fields.Many2one(
        'res.currency', string="Divisa")
    in_percentage_amount_2 = fields.Float(string='Porcentaje')
    in_is_expense_2 = fields.Boolean(string='Calcular gastos?')
    in_min_amount_2 = fields.Float(string='Monto mínimo')
    in_max_amount_2 = fields.Float(string='Monto máximo')
    in_field_ids_2 = fields.Many2many(
        'ir.model.fields', 'in_2_ir_model_fields_base_rate_rel', 'rate_id', 'field_id', string='Campos', domain=_set_domain)
    in_fixed_amount_2 = fields.Float(string='Cuota fija')
    in_container_amount_2 = fields.Float(string='Importe por contenedor')
    out_product_id_2 = fields.Many2one(
        'product.product', string="Producto en factura")
    out_apply_on_2 = fields.Selection(
        selection=[('percentage', 'Porcentaje'),
                   ('fixed', 'Cuota fija'),
                   ('container', 'Contenedor')],
        string='Aplica por')
    out_currency_id_2 = fields.Many2one(
        'res.currency', string="Divisa")
    out_percentage_amount_2 = fields.Float(string='Porcentaje')
    out_is_expense_2 = fields.Boolean(string='Calcular gastos?')
    out_min_amount_2 = fields.Float(string='Monto mínimo')
    out_max_amount_2 = fields.Float(string='Monto máximo')
    out_field_ids_2 = fields.Many2many(
        'ir.model.fields', 'out_2_ir_model_fields_base_rate_rel', 'rate_id', 'field_id', string='Campos', domain=_set_domain)
    out_fixed_amount_2 = fields.Float(string='Cuota fija')
    out_container_amount_2 = fields.Float(string='Importe por contenedor')
    other_rate_ids = fields.One2many(
        'base.rate.other', 'base_rate_id', string='Otros conceptos')

    @api.onchange('in_apply_on_1', 'in_apply_on_2', 'out_apply_on_1', 'out_apply_on_2')
    def onchange_apply_on(self):
        for rec in self:
            if rec.in_apply_on_1 != 'percentage':
                rec.in_is_expense_1 = False
            if rec.in_apply_on_2 != 'percentage':
                rec.in_is_expense_2 = False
            if rec.out_apply_on_1 != 'percentage':
                rec.out_is_expense_1 = False
            if rec.out_apply_on_2 != 'percentage':
                rec.out_is_expense_2 = False

    def compute_rate(self, type, obj):
        if type == '1':
            result = self.import_compute(obj)
        else:
            result = self.export_compute(obj)

        if self.other_rate_ids:
            result['product_id_3'] = self.other_rate_ids
        return result

    def import_compute(self, obj):
        print(obj.rate_id.in_apply_on_1)
        params = {
            'apply_on': self.in_apply_on_1,
            'product_id': self.in_product_id_1,
            'currency_id': self.in_currency_id_1,
            'is_expense': self.in_is_expense_1,
            'percentage_amount': self.in_percentage_amount_1,
            'field_ids': self.in_field_ids_1,
            'min_amount': self.in_min_amount_1,
            'max_amount': self.in_max_amount_1,
            'fixed_amount': self.in_fixed_amount_1,
            'container_amount': self.in_container_amount_1,
            'apply_on_2': self.in_apply_on_2,
            'product_id_2': self.in_product_id_2,
            'currency_id_2': self.in_currency_id_2,
            'is_expense_2': self.in_is_expense_2,
            'percentage_amount_2': self.in_percentage_amount_2,
            'field_ids_2': self.in_field_ids_2,
            'min_amount_2': self.in_min_amount_2,
            'max_amount_2': self.in_max_amount_2,
            'fixed_amount_2': self.in_fixed_amount_2,
            'container_amount_2': self.in_container_amount_2,
        }
        return self.general_compute(params, obj)

    def export_compute(self, obj):
        print(self.out_apply_on_1)
        params = {
            'apply_on': self.out_apply_on_1,
            'product_id': self.out_product_id_1,
            'currency_id': self.out_currency_id_1,
            'is_expense': self.out_is_expense_1,
            'percentage_amount': self.out_percentage_amount_1,
            'field_ids': self.out_field_ids_1,
            'min_amount': self.out_min_amount_1,
            'max_amount': self.out_max_amount_1,
            'fixed_amount': self.out_fixed_amount_1,
            'container_amount': self.out_container_amount_1,
            'apply_on_2': self.out_apply_on_2,
            'product_id_2': self.out_product_id_2,
            'currency_id_2': self.out_currency_id_2,
            'is_expense_2': self.out_is_expense_2,
            'percentage_amount_2': self.out_percentage_amount_2,
            'field_ids_2': self.out_field_ids_2,
            'min_amount_2': self.out_min_amount_2,
            'max_amount_2': self.out_max_amount_2,
            'fixed_amount_2': self.out_fixed_amount_2,
            'container_amount_2': self.out_container_amount_2,
        }
        return self.general_compute(params, obj)

    def general_compute(self, params, obj):
        vals = {}
        # Honorarios Rate
        print(params)
        vals['product_id'] = params['product_id']
        vals['currency_id'] = params['currency_id']
        if params['apply_on'] == 'percentage':
            if params['percentage_amount'] <= 0.00:
                raise UserError(_
                                ("El porcentaje de la tarifa por servicios de honorarios es: %s", str(
                                    params['percentage_amount']))
                                )
            if params['field_ids'] == False:
                raise UserError(_
                                ("Valor de Campos en la tarifa es vacío o nulo. Por favor verifique la información en la referencia SIR"))
            computed_amount = self.percentage_compute(
                params['field_ids'], params['percentage_amount'], params['is_expense'], obj)
            # vals['product_id'] = params['product_id']
            vals['amount_rate'] = computed_amount
            # vals['currency_id'] = params['currency_id']
        if params['apply_on'] == 'fixed':
            if params['fixed_amount'] <= 0.00:
                raise UserError(_
                                ("El valor de Cuota fija por servicios de honorarios es: %s", str(
                                    params['fixed_amount']))
                                )
            # vals['product_id'] = params['product_id']
            vals['amount_rate'] = params['fixed_amount']
            # vals['currency_id'] = params['currency_id']
        if params['apply_on'] == 'container':
            if params['container_amount'] <= 0.00:
                raise UserError(_
                                ("El valor Importe por contenedor en servicios de honorarios es: %s", str(
                                    params['container_amount']))
                                )
            vals['container_amount'] = params['container_amount']
        # Complementario Rate
        vals['product_id_2'] = params['product_id_2']
        vals['currency_id_2'] = params['currency_id_2']
        if params['apply_on_2'] == 'percentage':
            if params['percentage_amount_2'] <= 0.00:
                raise UserError(_
                                ("El porcentaje de la tarifa por servicios complementarios es: %s", str(
                                    params['percentage_amount_2']))
                                )
            if params['field_ids_2'] == False:
                raise UserError(_
                                ("Valor de Campos en la tarifa es vacío o nulo. Por favor verifique la información en la referencia SIR"))
            computed_amount = self.percentage_compute(
                params['field_ids_2'], params['percentage_amount_2'], params['is_expense_2'], obj)
            
            vals['amount_rate_2'] = computed_amount
        if params['apply_on_2'] == 'fixed':
            if params['fixed_amount_2'] <= 0.00:
                raise UserError(_
                                ("El valor de Cuota fija por servicios complementarios es: %s", str(
                                    params['fixed_amount_2']))
                                )
            vals['amount_rate_2'] = params['fixed_amount_2']
        if params['apply_on_2'] == 'container':
            if params['container_amount_2'] <= 0.00:
                raise UserError(_
                                ("El valor Importe por contenedor en servicios complementarios es: %s", str(
                                    params['container_amount_2']))
                                )
            vals['container_amount_2'] = params['container_amount_2']

        return vals

    def percentage_compute(self, fields, percentage_amount, is_expense, obj):
        acum = 0.00
        ctx = self._context
        for item in fields:
            field_name = item.name
            acum += obj.sir_id.mapped(field_name)[0]
        if is_expense and ctx.get('inv_id', False):
            to_agency_acum = 0.00
            for expense_line in obj.partner_expense_line_ids:
                if not expense_line.to_agency:
                    to_agency_acum += expense_line.total_expense
            acum += to_agency_acum
        else:
            acum += obj.amount_total
        if acum == 0.00:
            raise UserError(_("Valor de importe en campos de la tarifa es invalido o igual a cero. Por favor verifique la información en la referencia"))
        return (acum * percentage_amount) / 100


class BaseRateOther(models.Model):
    _name = 'base.rate.other'
    _rec_name = "name"

    name = fields.Char(string='Descripción')
    base_rate_id = fields.Many2one('base.rate', string="Tarifa")
    product_id = fields.Many2one('product.product', string="Producto")
    amount = fields.Monetary(string='Importe')
    currency_id = fields.Many2one('res.currency', string="Moneda")
    notes = fields.Text(string='Observaciones')
