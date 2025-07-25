from odoo import models,fields,api
from odoo.tools import get_lang

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    transport_request_id = fields.Many2one(
        'transport.request', string="Request Number")
    load_order_id = fields.Many2one(
        'load.order', string="Load Order")
    request_purchase = fields.Boolean("Transport Request")
    # request_beneficiary = fields.Char(
    #     related="sir_id.customer", string="Beneficiary")
    request_beneficiary_id = fields.Many2one(
        'res.partner', related="sir_id.partner_id", string="Beneficiary")
    # request_purchase_num = fields.Char(
    #     related="transport_request_id.name", string="Request Number")
    request_purchase_vehicle = fields.Char("Economic")
    request_purchase_tow = fields.Char("Trailer")
    purchase_origin_id = fields.Many2one(
        'res.partner', string="Origen",
        related="transport_request_id.company_shipper_id")
    purchase_destiny_id = fields.Many2one(
        'res.partner', string="Destination",
        related="transport_request_id.company_deliver_id")
    purchase_vehicle_tag = fields.Char("Vehicle Tag")
    purchase_dolly = fields.Char("Dolly")
    purchase_chassis = fields.Char("Chassis 1")
    purchase_chassis2 = fields.Char("Chassis 2")
    purchase_departure_date = fields.Datetime("Date and time of departure")
    purchase_arrive_date = fields.Datetime("Date and time of arrival")

    @api.model_create_multi
    def create(self, vals_list):
        order_ids = super(PurchaseOrder, self).create(vals_list)
        for order in order_ids:
            if order.load_order_id:
                order.load_order_id.write({
                    'purchase_id': order.id})
                # product_ids = order.order_line.mapped('product_id')
                # concept_line = order.load_order_id.concept_line_ids.filtered(
                #     lambda c: not c.purchase_line_id and c.product_id and \
                #         c.product_id.id in product_ids.ids)
                # if concept_line:
                #     concept_line.sudo().unlink()
        return order_ids

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('product_qty', 'product_uom', 'company_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        super(PurchaseOrderLine, self)._compute_price_unit_and_date_planned_and_name()
        for line in self:
            if not line.product_id or line.invoice_lines or not line.company_id:
                continue
            if not self.env.context.get('default_load_order_id') or \
                not self.env.context.get('default_order_line'):
                continue
            for ol in self.env.context.get('default_order_line'):
                if len(ol) != 3:
                    continue
                if isinstance(ol[2], dict):
                    if ol[2].get('product_id') != line.product_id.id:
                        continue
                    if ol[2].get('price_unit') != line.price_unit:
                        line.price_unit = ol[2].get('price_unit')
                    if not line.name:
                        product_lang = line.product_id.with_context(
                            lang=get_lang(self.env, self.partner_id.lang).code,
                            partner_id=line.partner_id.id,
                            company_id=line.company_id.id,
                        )
                        line.name = line._get_product_purchase_description(product_lang)
