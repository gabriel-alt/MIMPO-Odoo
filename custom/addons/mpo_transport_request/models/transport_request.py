from odoo import fields, models, api, _
from odoo.exceptions import UserError
import json


class TransportRequest(models.Model):
    _name = "transport.request"
    _description = "Transport Request"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        'Order', required=True, index='trigram', copy=False, default='New')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)
    state = fields.Selection(
        selection=[
            ('0_new', 'New'),
            ('1_progress', 'In progress'),
            ('3_assigned1', 'Assigned1'),
            ('3_assigned2', 'Assigned2'),
            ('3_assigned3', 'Assigned3'),
            ('5_monitoring', 'Monitoring'),
            ('7_pod1', 'Pending POD1'),
            ('7_pod2', 'Pending POD2'),
            ('9_ended', 'Ended'),
        ],
        string='Status', required=True, readonly=True,
        copy=False, tracking=True, default='0_new',)
    billing_reference_id = fields.Many2one(
        'load.order', string='Billing Reference', copy=False, readonly=True)
    load_order_ids = fields.One2many(
        'load.order', 'transport_request_id', copy=False, readonly=True)
    #Company to Bill
    company_bill_id = fields.Many2one(
        'res.partner', domain="[('is_company', '=', True)]",
        string="Company Bill")
    company_bill_vat = fields.Char(
        string='Tax ID to Bill',
        related='company_bill_id.vat', readonly=True)
    # company_bill_shipping_id = fields.Many2one(
    #     comodel_name='res.partner',
    #     string="Address to Bill",
    #     compute='_compute_company_bill_shipping_contact_id',
    #     store=True, readonly=False, precompute=True,
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    company_bill_contact_id = fields.Many2one(
        comodel_name='res.partner',
        string="Contact to Bill",
        compute='_compute_company_bill_shipping_contact_id',
        store=True, readonly=False, precompute=True,
        domain="[('parent_id', '=', company_bill_id), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    company_bill_email = fields.Char(
        string="Email to Bill",
        related='company_bill_id.email', readonly=True)
    company_bill_phone = fields.Char(
        string="Phone to Bill",
        related='company_bill_id.phone', readonly=True)
    #Company Shipper
    company_shipper_id = fields.Many2one(
        'res.partner', domain="[('is_company', '=', True)]",
        string="Company Shipper")
    company_shipper_vat = fields.Char(
        string='Shipper Tax ID',
        related='company_shipper_id.vat', readonly=True)
    # company_shipper_shipping_id = fields.Many2one(
    #     comodel_name='res.partner',
    #     string="Shipper Address",
    #     compute='_compute_company_shipper_shipping_contact_id',
    #     store=True, readonly=False, precompute=True,
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    company_shipper_contact_id = fields.Many2one(
        comodel_name='res.partner',
        string="Shipper Contact",
        compute='_compute_company_shipper_shipping_contact_id',
        store=True, readonly=False, precompute=True,
        domain="[('parent_id', '=', company_shipper_id), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    company_shipper_email = fields.Char(
        string="Shipper Email",
        related='company_shipper_id.email', readonly=True)
    company_shipper_phone = fields.Char(
        string="Shipper Phone",
        related='company_shipper_id.phone', readonly=True)
    pickup_date = fields.Datetime()
    # load_reference = fields.Many2one('load.order')
    #DELIVERY
    deliver_date = fields.Date()
    company_deliver_id = fields.Many2one(
        'res.partner', domain="[('is_company', '=', True)]",
        string="Company Deliver")
    company_deliver_vat = fields.Char(
        string='Deliver Tax ID',
        related='company_deliver_id.vat', readonly=True)
    # company_deliver_shipping_id = fields.Many2one(
    #     comodel_name='res.partner',
    #     string="Deliver Address",
    #     compute='_compute_company_deliver_shipping_contact_id',
    #     store=True, readonly=False, precompute=True,
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    company_deliver_contact_id = fields.Many2one(
        comodel_name='res.partner',
        string="Deliver Contact",
        compute='_compute_company_deliver_shipping_contact_id',
        store=True, readonly=False, precompute=True,
        domain="[('parent_id', '=', company_deliver_id), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    company_deliver_email = fields.Char(
        string="Deliver Email",
        related='company_deliver_id.email', readonly=True)
    company_deliver_phone = fields.Char(
        string="Deliver Phone",
        related='company_deliver_id.phone', readonly=True)
    rate_service_id = fields.Many2one(
        'customer.rate.service', string="Rate Service")
    #SPECIAL INSTRUCTIONS
    load_instructions = fields.Text()
    observations_load = fields.Text()
    add_equipment = fields.Text()
    load_rate = fields.Float()
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id', store=True, readonly=False, precompute=True,
        help="The load's currency.")
    add_costs = fields.Float()
    load_total = fields.Float()
    load_imo = fields.Boolean()
    load_custody = fields.Char()
    load_custody_id = fields.Many2one('custody.type', string='Load Custody')
    load_comment = fields.Char()
    #CUSTOM BROKER
    aa_cb = fields.Char(string="A.A./C.B.")
    company_broker_id = fields.Many2one(
        'res.partner', domain="[('is_company', '=', True)]",
        string="Company Broker")
    company_broker_vat = fields.Char(
        string='Broker Tax ID',
        related='company_broker_id.vat', readonly=True)
    # company_broker_shipping_id = fields.Many2one(
    #     comodel_name='res.partner',
    #     string="Broker Address",
    #     compute='_compute_company_broker_shipping_contact_id',
    #     store=True, readonly=False, precompute=True,
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    company_broker_contact_id = fields.Many2one(
        comodel_name='res.partner',
        string="Broker Contact",
        compute='_compute_company_broker_shipping_contact_id',
        store=True, readonly=False, precompute=True,
        domain="[('parent_id', '=', company_broker_id), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    company_broker_email = fields.Char(
        string="Broker Email",
        related='company_broker_id.email', readonly=True)
    company_broker_phone = fields.Char(
        string="Broker Phone",
        related='company_broker_id.phone', readonly=True)
    #LOAD DETAIL OF GOODS
    load_detail_goods_ids = fields.One2many(
        'transport.request.detail.goods', 'transport_request_id',
        string='Load Detail of Goods', copy=True)
    #TRANSPORT DETAIL (item list)
    transport_detail_line_ids = fields.One2many(
        'transport.request.detail.line', 'transport_request_id',
        string='Transport Detail Lines', copy=True)
    #Related Purchase
    purchase_ids = fields.One2many(
        'purchase.order', 'transport_request_id', copy=False, readonly=True)
    #field for domain
    sir_ref_ids = fields.Many2many(
        'sir.ref', 'compute_transport_request_sir_ref',
        compute="_compute_transport_sir_ref_ids")

    @api.depends('load_detail_goods_ids.sir_request_id')
    def _compute_transport_sir_ref_ids(self):
        for this in self:
            sir_ref = []
            for line in this.load_detail_goods_ids:
                if line.sir_request_id and \
                    line.sir_request_id.id not in sir_ref:
                    sir_ref.append(line.sir_request_id.id)
            this.update({'sir_ref_ids': [(6, 0, sir_ref)]})

    @api.depends('company_id')
    def _compute_currency_id(self):
        for this in self:
            this.currency_id = this.company_id.currency_id

    @api.depends('company_bill_id')
    def _compute_company_bill_shipping_contact_id(self):
        for order in self:
            if order.company_bill_id:
                partner_address = order.company_bill_id.address_get(
                    ['delivery', 'invoice'])
                order.company_bill_contact_id = partner_address['invoice']
            else:
                order.company_bill_contact_id = False

    @api.depends('company_shipper_id')
    def _compute_company_shipper_shipping_contact_id(self):
        for order in self:
            if order.company_shipper_id:
                partner_address = order.company_shipper_id.address_get(
                    ['delivery', 'invoice'])
                order.company_shipper_contact_id = partner_address['invoice']
            else:
                order.company_shipper_contact_id = False

    @api.depends('company_deliver_id')
    def _compute_company_deliver_shipping_contact_id(self):
        for order in self:
            if order.company_deliver_id:
                partner_address = order.company_deliver_id.address_get(
                    ['delivery', 'invoice'])
                order.company_deliver_contact_id = partner_address['invoice']
            else:
                order.company_deliver_contact_id = False

    @api.depends('company_broker_id')
    def _compute_company_broker_shipping_contact_id(self):
        for order in self:
            if order.company_broker_id:
                partner_address = order.company_broker_id.address_get(
                    ['delivery', 'invoice'])
                order.company_broker_contact_id = partner_address['invoice']
            else:
                order.company_broker_contact_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company_id = vals.get(
                'company_id', self.default_get(['company_id'])['company_id'])
            self_comp = self.with_company(company_id)
            if vals.get('name', 'New') == 'New':
                vals['name'] = self_comp.env['ir.sequence'].next_by_code(
                    'transport.request') or '/'
        return super(TransportRequest, self_comp).create(vals)

    def action_progress(self):
        new_transport = self.filtered(lambda t: t.state == '0_new')
        if new_transport:
            new_transport.write({'state': '1_progress'})
            assigned1 = new_transport.filtered(lambda t: t.transport_detail_line_ids)
            return assigned1.write({'state': '3_assigned1'})
        return False

    def action_assigned1(self):
        progress_transport = self.filtered(lambda t: t.state == '1_progress')
        if any(not p.transport_detail_line_ids for p in progress_transport):
            raise UserError(_(
                "Please set Transport Detail before move to Assigned 1."))
        return progress_transport.write({'state': '3_assigned1'})

    def action_assigned2(self):
        transports = self.filtered(lambda t: t.state == '3_assigned1')
        if any(not p.transport_detail_line_ids for p in transports):
            raise UserError(_(
                "Please set Transport Detail before move to Assigned 1."))
        return transports.write({'state': '3_assigned2'})

    def action_assigned3(self):
        transports = self.filtered(lambda t: t.state == '3_assigned2')
        if any(not p.transport_detail_line_ids for p in transports):
            raise UserError(_(
                "Please set Transport Detail before move to Assigned 1."))
        return transports.write({'state': '3_assigned3'})

    def action_pod1(self):
        transports = self.filtered(lambda t: t.state == '5_monitoring')
        return transports.write({'state': '7_pod1'})

    def action_pod2(self):
        transports = self.filtered(lambda t: t.state == '7_pod1')
        return transports.write({'state': '7_pod2'})

    def action_ended(self):
        transports = self.filtered(lambda t: t.state == '7_pod2')
        return transports.write({'state': '9_ended'})

    def process_create_load_order(self):
        self.ensure_one()
        load_id = self.env['load.order'].create({
            'name': self.name,
            'transport_request_id': self.id})
        if load_id:
            self.write({'billing_reference_id': load_id.id})

    def action_create_load_order(self):
        for this in self:
            if this.load_order_ids:
                raise UserError(_("Load Order already created."))
        load = 1
        load_list = []
        for line in self.transport_detail_line_ids:
            line_vals = line._prepare_vals_load_order()
            line_vals['name'] = self.name + '/' + str(load)
            load_id = self.env['load.order'].create(line_vals)
            load_list.append(load_id.id)
            load += 1
        if load_list:
            self.write({'state': '5_monitoring'})
        return {
            'name': _('Load order'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'load.order',
            'domain': [('id', 'in', load_list)],
            'context': {'create': 0, 'delete': 0},
        }

    def action_unit_assignment_rfq(self):
        sorted_transport_details_ids = self.transport_detail_line_ids.sorted(
            key=lambda ln:ln.assign_date)
        if len(sorted_transport_details_ids.ids)> 1:
            sorted_transport_details_ids = sorted_transport_details_ids[0]
        sir_request_id = sorted_transport_details_ids.sir_request_ids
        
        default_val = {
            'default_transport_request_id': self.id,
            'default_request_purchase': True,
            'default_sir_id': sir_request_id and sir_request_id[0].id or False
        }
        return {
            'name': "Request for Quotation",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': default_val,
        }

    def action_view_purchase_order(self):
        return {
            'name': _('Purchase order'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,kanban,form',
            'res_model': 'purchase.order',
            'domain': [('transport_request_id', 'in', self.ids)],
            'context': {'quotation_only': True, 'create': 0},
        }

    def action_view_load_order(self):
        return {
            'name': _('Load order'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,kanban,form',
            'res_model': 'load.order',
            'domain': [('transport_request_id', 'in', self.ids)],
            'context': {'create': 0, 'delete': 0},
        }

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Transport Request - %s' % (self.name)

    def _get_editable_transport_fields(self):
        return ['company_bill_id', 'company_bill_contact_id',
                'company_shipper_id', 'company_shipper_contact_id',
                'company_deliver_id', 'company_deliver_contact_id',
                'deliver_date', 'load_instructions', 'observations_load',
                'add_equipment', 'load_rate', 'currency_id',
                'add_costs', 'load_total', 'load_imo',
                'load_custody_id', 'load_comment', 'aa_cb',
                'company_broker_id', 'company_broker_contact_id']

    # @api.model
    # def _get_view(self, view_id=None, view_type='form', **options):
    #     arch, view = super(TransportRequest, self)._get_view(
    #         view_id, view_type, **options)
    #     if view_type == 'form' and self.env.user.has_group(
    #         'mpo_transport_request.traffic_executive_group_user'):
    #         list_fields = self._get_editable_transport_fields()
    #         for f in list_fields:
    #             for node in arch.xpath("//field[@name='%s']"%(f)):
    #                 try:
    #                     modifiers = json.loads(node.attrib.get('attrs'))
    #                 except:
    #                     try:
    #                         modifiers = node.attrib.get('attrs')
    #                     except:
    #                         modifiers = {}
    #                 if not modifiers:
    #                     continue
    #                 if isinstance(modifiers, dict) and \
    #                     modifiers.get('readonly'):
    #                     ro = modifiers.pop('readonly')
    #                     node.set('attrs', json.dumps(modifiers))
    #                     node.set('modifiers', json.dumps(modifiers))
    #                 elif isinstance(modifiers, str) and 'readonly' in modifiers:
    #                     node.set('attrs', json.dumps({}))
    #                     node.set('modifiers', json.dumps({}))
    #     return arch, view

class TransportRequestDetailGoods(models.Model):
    _name = "transport.request.detail.goods"
    _description = "Transport Request Detail of Goods"

    transport_request_id = fields.Many2one(
        'transport.request', string='Transport Request',
        index=True, required=True, ondelete='cascade', copy=False)
    sir_request_id = fields.Many2one(
        'sir.ref', string='SIR', ondelete='restrict')
    pedimento = fields.Char(related='sir_request_id.pedimento', readonly=True)
    qty_request = fields.Float(string="Quantity")
    scheme_request = fields.Char(string='Scheme')
    kum_request = fields.Char(string='K.U.M.')
    cubication_request = fields.Float(string='Cubication')
    long_request = fields.Float(string='Long')
    high_request = fields.Float(string='High')
    width_request = fields.Float(string='Width')
    keyprod_request = fields.Char(string='Product Key')
    gross_request = fields.Float(string='Gross Weight')
    packages_request = fields.Char(string='Packages')
    stamp_request = fields.Char(string='Stamps')
    date_delay_request = fields.Date(string='Date of Delay')
    chm_request = fields.Char(string='C.H.M.')
    sat_request = fields.Char(string='Sat Description')
    bol_request = fields.Char(string='BOL')
    container_request = fields.Char(string='Container')
    t_container_request = fields.Char(string='T.Container')
    packing_request = fields.Char(string='Key Type Packing')
    commodity_request = fields.Char(string='Commodity')
    fraction_request = fields.Char(string='Fraction')
    hazardous_request = fields.Char(string='Hazardous Material')
    container2 = fields.Char(string='Container 2')
    importer = fields.Char()

    # def _prepare_vals_load_order(self):
    #     self.ensure_one()
    #     vals = {
    #         'transport_request_goods_id': self.id,
    #         'transport_request_id': self.transport_request_id.id,
    #     }
    #     return vals

class TransportRequestDetailLine(models.Model):
    _name = "transport.request.detail.line"
    _description = "Transport Request Detail Line"

    transport_request_id = fields.Many2one(
        'transport.request', string='Transport Request',
        index=True, required=True, ondelete='cascade', copy=False)
    local_foreign = fields.Boolean(
        string='Local', related="transport_company_id.solo_transporte",
        readonly=True, store=True)
    transport_partner_id = fields.Many2one(
        'res.partner', string="Transport Contact")
    transport_company_id = fields.Many2one(
        'res.company', string="Transport")
    solo_transporte = fields.Boolean(related='transport_company_id.solo_transporte')
    unit_type_id = fields.Many2one('unit.type', string='Unit Type')
    tarif_element_id = fields.Many2one(
        'customer.rate.tarif.element', string='Tarif Element')
    assign_date = fields.Datetime()
    # sir_request_id = fields.Many2one(
    #     'sir.ref', string='SIR', ondelete='restrict')
    sir_request_ids = fields.Many2many(
        'sir.ref', string='SIR', ondelete='restrict')
    vehicle_economic = fields.Char("Economic")
    vehicle_plates = fields.Char("Plates")
    vehicle_operator = fields.Char('Operator')

    def _prepare_vals_load_order(self):
        self.ensure_one()
        product_lines = []
        if self.tarif_element_id:
            product_vals = {
                'product_id': self.tarif_element_id.product_id.id,
                'vendor_price': 0.0,
                'customer_price': self.tarif_element_id.customer_price,
            }
            if self.tarif_element_id.vendor_cost_ids:
                cost_ids = self.tarif_element_id.vendor_cost_ids.filtered(
                    lambda c: c.company_id == self.transport_company_id)
                if cost_ids:
                    product_vals['vendor_price'] = cost_ids[0].price
            product_lines.append((0, 0, product_vals))
        vals = {
            'transport_request_line_id': self.id,
            'transport_request_id': self.transport_request_id.id,
            'concept_line_ids': product_lines,
        }
        return vals
