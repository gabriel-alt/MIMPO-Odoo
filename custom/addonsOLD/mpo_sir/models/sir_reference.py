# -*- coding: utf-8 -*-
""" SIR Reference """
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class CveTransporte(models.Model):
    """ Define SIR Ref """

    _name = 'sir.ref'
    _inherit = ['base.api', 'mail.thread', 'mail.activity.mixin']
    _rec_name = "number"

    ref_id = fields.Integer(string='ID referencia SIR')
    number = fields.Char(string='Número referencia SIR')
    pedimento = fields.Char(string='Número de pedimento')
    customer = fields.Char(string='Clave del cliente')
    # partner_id = fields.Many2one('res.partner', string='Cliente',
    #                              compute='_compute_sir_customer_id', store=True)
    partner_id = fields.Many2one('res.partner', string='Cliente')
    operation_type = fields.Integer(
        string='Tipo de operación del pedimento', help="1- Importación 2- Exportación")
    ref_document = fields.Char(string='Clave del tipo de documento')
    total_weight = fields.Float(string='Peso bruto de la operación')
    total_custom_house = fields.Float(string='Valor aduana del pedimento')
    invoice_value = fields.Float(string='Valor factura del pedimento')
    total_sale = fields.Float(string='Valor comercial del pedimento')
    type_rate = fields.Float(string='Tipo de cambio del pedimento')
    container_qty = fields.Integer(string='Cantidad de contenedores de la operación')
    sliced_group = fields.Integer(string='Cantidad de fracciones desagrupadas')
    non_sliced_group = fields.Integer(string='Cantidad de fracciones agrupadas')
    non_paid_tax = fields.Float(string='Importe de los impuestos no pagados')
    paid_tax = fields.Float(string='Importe del los impuestos pagados por el cliente')
    guide_qty = fields.Integer(string='Cantidad de guias del pedimento')
    total_package = fields.Integer(string='Total de bultos del pedimento')
    total_padlock = fields.Integer(string='Total de candados de la operación')
    total_remittance = fields.Integer(string='Total de remesas de la operación')
    total_invoice = fields.Integer(string='Total de Facturas de la operación')
    total_cove = fields.Integer(string='Total de los coves de la operación')
    total_part = fields.Integer(string='Total de partes de la operación')
    total_eDocument = fields.Integer(string='Cantidad de edocuments de la referencia')
    total_taxes = fields.Float(string='Total de impuestos pagados en efectivo del pedimento')
    amount_dta = fields.Float(string='Importe de impuestos DTA del pedimento')
    amount_adv = fields.Float(string='Importe de impuestos ADV del pedimento')
    amount_ieps = fields.Float(string='Importe de impuestos IEPS del pedimento')
    amount_other = fields.Float(string='Importe de otros impuestos del pedimento')
    amount_iva = fields.Float(string='Importe de impuestos IVA del pedimento')
    amount_insurance = fields.Float(string='Importe de incrementables del pedimento (seguros)')
    amount_expense = fields.Float(string='Importe de incrementables del pedimento (Gastos)')
    amount_ded_other = fields.Float(string='Importe de otros incrementables del pedimento')
    total_inc = fields.Float(string='Total de incrementables')
    amount_ph = fields.Float(string='Importe total para el pago hecho')
    date_ph = fields.Char(string='Fecha en que se realizó el pago de pedimento')
    pece_account = fields.Boolean(
        string='Pagado con cuenta PECE')
    pedimento_date = fields.Char(string='Fecha en que se pago el pedimento')
    custom_house = fields.Char(string='Aduana')
    house_id = fields.Many2one('custom.house', string='Clave de aduana')
    pedimento_invoice = fields.Char(string='Numeros de facturas del pedimento')
    number_mark = fields.Char(string='Marcas y numero de la referencia')
    ware = fields.Char(string='Descripción de la mercancia')
    reception = fields.Char(string='Recepción')
    order_number = fields.Char(string='Número de pedido')
    ship = fields.Char(string='Buque')
    supplier = fields.Char(string='Nombre de proveedor')
    move_ids = fields.One2many('account.move', 'sir_id', copy=False)
    sale_ids = fields.One2many('sale.order', 'sir_id', copy=False)
    account_move_count = fields.Integer(compute='_compute_account_move_count')
    sale_order_count = fields.Integer(compute='_compute_sale_order_count')
    account_analytic_id = fields.Many2one(
        'account.analytic.account', string="Plan Analítico", copy=False)
    state = fields.Selection(
        [('open', 'Abierto'), ('close', 'Cerrado')], readonly=False, index=True, copy=False,
        tracking=1, default='open')

    patent_code = fields.Char("Patente")

    # @api.depends('customer')
    # def _compute_sir_customer_id(self):
    #     """ Compute Partner """

    #     for record in self:
    #         partner_id = False
    #         if record.customer:
    #             partner = self.env['res.partner'].search(
    #                 [('partner_ref','=', record.customer)], limit=1)
    #             partner_id = partner.id if partner else partner_id
    #         record.partner_id = partner_id

    @api.onchange('custom_house')
    def _compute_sir_custom_house(self):
        """ Onchange Partner Aduana"""

        for record in self:
            if record.partner_id:
                record.partner_id.contact_number = record.custom_house

    @api.depends('move_ids')
    def _compute_account_move_count(self):
        """ Count Account Move Related to the SIR Reference """

        for record in self:
            record.account_move_count = len(record.move_ids)

    @api.depends('sale_ids')
    def _compute_sale_order_count(self):
        """ Count Sale Order Related to the SIR Reference """

        for record in self:
            record.sale_order_count = len(record.sale_ids)

    def prepare_analytic_vals(self):
        """ Prepare Analytic Account Values """

        self.ensure_one()
        # TODO: change method to get company_id and plan_id once it's possible to create SIR Reference
        # for various companies
        partner_id = self.partner_id
        if not partner_id and self.customer:
            partner_id = self.env['res.partner'].search(
                [('partner_ref','=', self.customer)], limit=1)
        return {'name': self.number,
                'company_id': self.env.user.company_id.sir_analytic_plan_id.company_id.id,
                'partner_id': partner_id and partner_id.id or False,
                'plan_id': self.env.user.company_id.sir_analytic_plan_id.id}

    def create_analytic(self):
        """ Create Analytic Account """

        for record in self:
            vals = record.prepare_analytic_vals()
            analytic = self.env['account.analytic.account'].create(vals)
            if not record.partner_id and vals.get('partner_id'):
                record.write({
                    'partner_id': vals.get('partner_id'),
                    'account_analytic_id': analytic.id})
            else:
                record.write({'account_analytic_id': analytic.id})

    def default_analytic_plan_validation(self):
        """ Validate Default Analytic Plan """

        # TODO: change method to get company once it's possible to create SIR Reference
        # for various companies
        company = self.env.user.company_id
        if not company.sir_analytic_plan_id:
            raise ValidationError(_(
                "Please Define Default Analytic Plan for SIR Reference Creation!"))

    @api.model_create_multi
    def create(self, vals_list):
        """ Inherit Create """

        self.default_analytic_plan_validation()
        sir_number = vals_list[0].get('number',False)
        sir_id = self.env['sir.ref'].search([
            ('number','=',sir_number)], limit=1)
        if sir_id:
            raise ValidationError(_("0"))
        for vals in vals_list:
            if vals.get('custom_house'):
                house_id = self.env['custom.house'].search([
                    ('number', '=', vals.get('custom_house'))], limit=1)
                if house_id:
                    vals['house_id'] = house_id.id
            if not vals.get('partner_id') and vals.get('customer'):
                partner_id = self.env['res.partner'].search([
                    ('partner_ref', '=', vals.get('customer'))], limit=1)
                if partner_id:
                    vals['partner_id'] = partner_id.id
        res = super(CveTransporte, self).create(vals_list)
        if res.customer and not res.partner_id:
            sir_partner_id = res.customer
            partner_id = self.env['res.partner'].search([
                ('partner_ref','=',sir_partner_id)], limit=1)
            if partner_id:
                vals_list[0]['partner_id'] = partner_id.id
        res.create_analytic()
        return res

    def write(self, vals):
        res = super(CveTransporte, self).write(vals)
        if self.env.context.get('skip_check_ref'):
            return res
        if vals.get('customer') or vals.get('partner_id'):
            for this in self:
                if this.customer != this.partner_id.partner_ref:
                    this.partner_id.write({'partner_ref': this.customer})
                elif this.customer and not this.partner_id:
                    partner_id = self.env['res.partner'].search([
                        ('partner_ref', '=', this.customer)], limit=1)
                    if partner_id:
                        this.with_context(skip_check_ref=True).write(
                            {'partner_id': partner_id.id})
        return res

    def action_view_move(self):
        """ This function returns an action that display Related Journal Entry """

        self.ensure_one()
        result = self.env["ir.actions.actions"]._for_xml_id('account.action_move_journal_line')
        result['context'] = {'default_sir_id': self.id, 'search_default_sir_id': self.id}
        if not self.move_ids or len(self.move_ids) > 1:
            result['domain'] = [('id', 'in', self.move_ids.ids)]
        elif len(self.move_ids) == 1:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            result['views'] = form_view + \
                [(state, view) for state, view in result.get('views', []) if view != 'form']
            result['res_id'] = self.move_ids.id
        return result

    def action_view_analytic(self):
        """ Return action to display Related Analytic Account """

        self.ensure_one()
        result = self.env["ir.actions.actions"]._for_xml_id(
            'analytic.action_account_analytic_account_form')
        result['context'] = {'default_sir_id': self.id, 'search_default_sir_id': self.id}
        res = self.env.ref('analytic.view_account_analytic_account_form', False)
        form_view = [(res and res.id or False, 'form')]
        result['views'] = form_view + \
            [(state, view) for state, view in result.get('views', []) if view != 'form']
        result['res_id'] = self.account_analytic_id.id
        return result

    def action_view_sales(self):
        """ This Function Returns an Action that Display Related Sales """

        self.ensure_one()
        result = self.env["ir.actions.actions"]._for_xml_id('sale.action_orders')
        result['context'] = {'default_sir_id': self.id, 'search_default_sir_id': self.id}
        if not self.sale_ids or len(self.sale_ids) > 1:
            result['domain'] = [('id', 'in', self.sale_ids.ids)]
        elif len(self.sale_ids) == 1:
            res = self.env.ref('sale.view_order_form', False)
            form_view = [(res and res.id or False, 'form')]
            result['views'] = form_view + \
                [(state, view) for state, view in result.get('views', []) if view != 'form']
            result['res_id'] = self.sale_ids.id
        return result

    def change_status(self):
        """ Change Status """

        self.ensure_one()
        self.state = 'open'

    def action_close_status(self):
        """ Change Close """
        self.ensure_one()
        self.state = 'close'
