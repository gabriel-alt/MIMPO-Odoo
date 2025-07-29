from odoo import fields, models, api
from datetime import datetime
from babel.dates import format_datetime, format_date
from odoo.tools.misc import formatLang, format_date as odoo_format_date, get_lang


class LoadOrder(models.Model):
    _name = "load.order"
    _description = "Load order"

    name = fields.Char(string="Order")
    folio = fields.Char(string='Folio System')
    transport_request_goods_id = fields.Many2one(
        'transport.request.detail.goods', string='Transport Request Goods',
        copy=False, readonly=True)
    transport_request_line_id = fields.Many2one(
        'transport.request.detail.line',
        string='Transport Request Detail Line', copy=False, readonly=True)
    transport_company_id = fields.Many2one(
        'res.company', string='Transport Company', readonly=True, store=True,
        related='transport_request_line_id.transport_company_id')
    transport_request_id = fields.Many2one(
        'transport.request', string='Transport Request',
        copy=False, readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True, store=True,
        related='transport_request_id.company_id')
    company_bill_id = fields.Many2one(
        'res.partner', string="Bill To", readonly=True,
        related='transport_request_id.company_bill_id')
    # company_shipper_shipping_id = fields.Many2one(
    #     'res.partner', string="Sender", readonly=True,
    #     related='transport_request_id.company_shipper_shipping_id')
    company_shipper_id = fields.Many2one(
        'res.partner', string="Origin", readonly=True,
        related='transport_request_id.company_shipper_id')
    company_deliver_id = fields.Many2one(
        'res.partner', string="Destination", readonly=True,
        related='transport_request_id.company_deliver_id')
    # company_bill_shipping_id = fields.Many2one(
    #     'res.partner', string="Recipient", readonly=True,
    #     related='transport_request_id.company_bill_shipping_id')
    # company_deliver_shipping_id = fields.Many2one(
    #     'res.partner', string="Deliver To", readonly=True,
    #     related='transport_request_id.company_deliver_shipping_id')
    company_deliver_contact_id = fields.Many2one(
        'res.partner', string="Contact Name", readonly=True,
        related='transport_request_id.company_deliver_contact_id')
    company_deliver_phone = fields.Char(
        string="Phone", readonly=True,
        related='transport_request_id.company_deliver_id.phone')
    sir_request_ids = fields.Many2many(
        'sir.ref', string='SIR Reference', readonly=True,
        compute='_compute_sir_request_unit_type')
    unit_type_ids = fields.Many2many(
        'unit.type', string='Unit Type', readonly=True,
        compute='_compute_sir_request_unit_type')
    # driver_order_id = fields.Many2one(
    #     'res.partner', string="Driver")
    driver = fields.Char()
    nombre_transpor = fields.Char()
    ####
    purchase_id = fields.Many2one(
        'purchase.order', string='Vendor', inverse='')
    sale_id = fields.Many2one(
        'sale.order', string='Client', inverse='')
    #Concept line
    concept_line_ids = fields.One2many(
        'load.order.concept.line', 'load_order_id',
        string='Load Order Concept Lines', copy=True, store=True,
        compute="", readonly=False)

    @api.depends(
        'transport_request_id', 'transport_request_goods_id',
        'transport_request_line_id')
    def _compute_sir_request_unit_type(self):
        for this in self:
            sir_request = []
            unit_type = []
            transport_id = this.transport_request_id
            if this.transport_request_line_id:
                sir_req_ids = this.transport_request_line_id.sir_request_ids
                sir_request = sir_req_ids.ids
            elif this.transport_request_goods_id:
                goods_id = this.transport_request_goods_id
                sir_request = goods_id.sir_request_id.ids
            elif transport_id and transport_id.load_detail_goods_ids:
                sir_request_ids = transport_id.load_detail_goods_ids.mapped(
                    'sir_request_id')
                sir_request = sir_request_ids.ids
            if this.transport_request_line_id:
                tarif_id = this.transport_request_line_id.tarif_element_id
                unit_type_ids = tarif_id.route_id.unit_type_id
                unit_type = unit_type_ids.ids
            elif transport_id and transport_id.transport_detail_line_ids:
                unit_type_ids = transport_id.transport_detail_line_ids.mapped(
                    'unit_type_id')
                unit_type = unit_type_ids.ids
            this.write({
                'sir_request_ids': [(6, 0, sir_request)],
                'unit_type_ids': [(6, 0, unit_type)]})

    # @api.depends('purchase_id', 'sale_id')
    # def _compute_concept_line_ids(self):
    #     for this in self:
    #         if not this.purchase_id and not this.sale_id:
    #             concepts = this.concept_line_ids.filtered(
    #                 lambda c: c.purchase_line_id or c.sale_line_id)
    #             concepts.unlink()
    #             continue
    #         concept_lines, exist_pol, exist_sol, exist_product = [], {}, {}, {}
    #         for concept in this.concept_line_ids:
    #             if not concept.purchase_line_id and not concept.sale_line_id:
    #                 continue
    #             if concept.purchase_line_id.id not in exist_pol:
    #                 exist_pol[concept.purchase_line_id.id] = concept
    #             if concept.sale_line_id.id not in exist_sol:
    #                 exist_sol[concept.sale_line_id.id] = concept
    #             if concept.product_id.id not in exist_product:
    #                 exist_product[concept.product_id.id] = concept
    #             if concept.purchase_line_id and concept.sale_line_id:
    #                 if concept.sale_line_id.order_id != this.sale_id and \
    #                     concept.purchase_line_id.order_id != this.purchase_id:
    #                     concept_lines.append((2, concept.id, False))
    #                 elif concept.sale_line_id.order_id != this.sale_id:
    #                     concept_lines.append((1, concept.id, {
    #                         'sale_line_id': False,
    #                         'customer_price': 0.0, 'customer_total': 0.0}))
    #                 elif concept.purchase_line_id.order_id != this.purchase_id:
    #                     concept_lines.append((1, concept.id, {
    #                         'purchase_line_id': False,
    #                         'vendor_price': 0.0, 'vendor_total': 0.0}))
    #             elif not concept.sale_line_id and \
    #                 concept.purchase_line_id.order_id != this.purchase_id:
    #                 concept_lines.append((2, concept.id, False))
    #             elif not concept.purchase_line_id and \
    #                 concept.sale_line_id.order_id != this.sale_id:
    #                 concept_lines.append((2, concept.id, False))
    #         new_vals = {}
    #         for pol in this.purchase_id.order_line:
    #             if not pol.product_id:
    #                 continue
    #             concept_vals = {}
    #             concept_id = False
    #             if pol.id in exist_pol:
    #                 concept_id = exist_pol.get(pol.id)
    #             elif pol.product_id.id in exist_product:
    #                 concept_id = exist_product.get(pol.product_id.id)
    #             if concept_id:
    #                 if pol.price_unit != concept_id.vendor_price:
    #                     concept_vals['vendor_price'] = pol.price_unit
    #                 if pol.price_subtotal != concept_id.vendor_total:
    #                     concept_vals['vendor_total'] = pol.price_subtotal
    #                 concept_id.write(concept_vals)
    #             else:
    #                 new_vals[pol.product_id.id] = {
    #                     'product_id': pol.product_id.id,
    #                     'purchase_line_id': pol.id,
    #                     'vendor_price': pol.price_unit,
    #                     'vendor_total': pol.price_subtotal,
    #                 }
    #         for sol in this.sale_id.order_line:
    #             if not sol.product_id:
    #                 continue
    #             concept_vals = {}
    #             concept_id = False
    #             if sol.id in exist_sol:
    #                 concept_id = exist_sol.get(sol.id)
    #             elif sol.product_id.id in exist_product:
    #                 concept_id = exist_product.get(sol.product_id.id)
    #             if concept_id:
    #                 if sol.price_unit != concept_id.customer_price:
    #                     concept_vals['customer_price'] = sol.price_unit
    #                 if sol.price_subtotal != concept_id.customer_total:
    #                     concept_vals['customer_total'] = sol.price_subtotal
    #                 concept_id.write(concept_vals)
    #             elif sol.product_id.id in new_vals:
    #                 new_vals[sol.product_id.id]['sale_line_id'] = sol.id
    #                 new_vals[sol.product_id.id][
    #                     'customer_price'] = sol.price_unit
    #                 new_vals[sol.product_id.id][
    #                     'customer_total'] = sol.price_subtotal
    #             else:
    #                 new_vals[sol.product_id.id] = {
    #                     'product_id': sol.product_id.id,
    #                     'sale_line_id': sol.id,
    #                     'customer_price': sol.price_unit,
    #                     'customer_total': sol.price_subtotal,
    #                 }
    #         for k, v in new_vals.items():
    #             concept_lines.append((0, 0, v))
    #         if concept_lines:
    #             this.update({'concept_line_ids': concept_lines})

    # @api.model_create_multi
    # def create(self, vals_list):
    #     load_ids = super(LoadOrder, self).create(vals_list)
    #     for load in load_ids:
    #         if load.transport_request_id:
    #             load.transport_request_id.write({
    #                 'billing_reference_id': load.id})
    #     return load_ids

    def action_create_purchase_order(self):
        self.ensure_one()
        default_val = {
            'default_transport_request_id': self.transport_request_id.id,
            'default_load_order_id': self.id,
            'default_request_purchase': True,
            'default_sir_id': self.sir_request_ids and \
                self.sir_request_ids[0].id or False
        }
        if self.transport_request_line_id:
            default_val['default_company_id'] = self.transport_company_id.id
            default_val['default_request_purchase_vehicle'] = self.transport_request_line_id.vehicle_economic
            if self.transport_request_line_id.tarif_element_id.vendor_cost_ids:
                cost_ids = self.transport_request_line_id.tarif_element_id.vendor_cost_ids.filtered(
                    lambda c: c.company_id == self.transport_company_id)
                if cost_ids:
                    default_val['default_partner_id'] = cost_ids[0].partner_id.id
        product_lines = []
        for line in self.concept_line_ids:
            product_vals = {
                'product_id': line.product_id.id,
                'price_unit': line.vendor_price,
                'product_uom': line.product_id.uom_po_id.id or line.product_id.uom_id.id,
            }
            product_lines.append((0, 0, product_vals))
        if product_lines:
            default_val['default_order_line'] = product_lines
        return {
            'name': "Request for Quotation",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': default_val,
        }

    def action_create_sale_order(self):
        self.ensure_one()
        default_val = {
            'default_transport_request_id': self.transport_request_id.id,
            'default_load_order_id': self.id,
            'default_request_purchase': True,
            'default_sir_id': self.sir_request_ids and \
                self.sir_request_ids[0].id or False
        }
        if self.transport_request_line_id:
            default_val['default_company_id'] = self.transport_company_id.id
            default_val['default_partner_id'] = self.company_bill_id.id
        product_lines = []
        for line in self.concept_line_ids:
            if line.product_id:
                product_vals = {
                    'display_type': False,
                    'product_id': line.product_id.id,
                    'name': line.product_id.get_product_multiline_description_sale(),
                    'price_unit': line.customer_price,
                    'product_uom_qty': 1.0,
                    'product_uom': line.product_id.uom_id.id,
                    'customer_lead': 1.0,
                    'sequence': 10,
                }
                product_lines.append((0, 0, product_vals))
        if product_lines:
            default_val['default_order_line'] = product_lines
        sale_id = self.env['sale.order'].with_context(default_val).create({})
        return {
            'name': "Quotation",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': sale_id.id,
            'target': 'current',
            'context': default_val,
        }

    def _get_report_base_filename(self):
        if len(self) == 1:
            return 'Load Order - %s' % (self.name)
        return 'Load Order'

    def _get_timenow_mex(self):
        today = fields.Date.today()
        format_month = lambda d: format_date(
            d, format='EEEE, dd MMMM yyyy', locale='es_MX')
        return format_month(today).title()

    def _get_concept_line_category(self):
        self.ensure_one()
        categ_vendor = {
            'fletes': 0.0, 'movimientos': 0.0, 'estadias': 0.0,
            'reexp': 0.0, 'logistic': 0.0, 'otros': 0.0, 'total': 0.0
        }
        categ_customer = {
            'fletes': 0.0, 'movimientos': 0.0, 'estadias': 0.0,
            'reexp': 0.0, 'logistic': 0.0, 'otros': 0.0, 'total': 0.0
        }
        for line in self.concept_line_ids:
            if line.category:
                categ_vendor[line.category] += line.vendor_total
                categ_customer[line.category] += line.customer_total
                categ_vendor['total'] += line.vendor_total
                categ_customer['total'] += line.customer_total
        return {'vendor': categ_vendor, 'customer': categ_customer}

class LoadOrderConceptLine(models.Model):
    _name = "load.order.concept.line"
    _description = "Load Order Concept Line"

    load_order_id = fields.Many2one(
        'load.order', string='Load Order',
        index=True, required=True, ondelete='cascade', copy=False)
    product_id = fields.Many2one(
        'product.product', string='Product', change_default=True,
        domain=[('purchase_ok', '=', True)], index='btree_not_null')
    purchase_line_id = fields.Many2one('purchase.order.line', readonly=False)
    sale_line_id = fields.Many2one('sale.order.line', readonly=False)
    category = fields.Selection(
        selection=[
            ('fletes', 'Fletes'),
            ('movimientos', 'Movimientos en falso'),
            ('estadias', 'Estadias por remolque'),
            ('reexp', 'Re-expedición de destino'),
            ('logistic', 'Logística inversa'),
            ('otros', 'Otros cargos'),
        ], default='fletes',)
    vendor_price = fields.Float(
        string='Vendor Fee', digits='Product Price')
    customer_price = fields.Float(
        string='Client Fee', digits='Product Price')
    vendor_total = fields.Float(
        string='Total Vendor Fee', digits='Product Price')
    customer_total = fields.Float(
        string='Total Client Fee', digits='Product Price')
    difference = fields.Float(
        string='Difference', digits='Product Price',
        compute="_compute_difference", store=True, precompute=True)

    @api.depends('vendor_total', 'customer_total')
    def _compute_difference(self):
        for line in self:
            line.difference = line.vendor_total - line.customer_total
