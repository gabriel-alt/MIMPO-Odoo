# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from odoo import api, fields, models, _
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class createsaleorder(models.TransientModel):
	_inherit = 'create.saleorder'

	gain_margin = fields.Float(
		string="Profit Margin (%)", related='partner_id.gain_margin')
	transport_request_id = fields.Many2one(
        'transport.request', string="Request Number")
	request_purchase = fields.Boolean("Transport Request")

	@api.model
	def default_get(self,  default_fields):
		res = super(createsaleorder, self).default_get(default_fields)
		record = self.env['purchase.order'].browse(
			self._context.get('active_ids',[]))
		if record.request_purchase:
			res['request_purchase'] = record.request_purchase
			res['transport_request_id'] = record.transport_request_id.id or False
			if record.request_beneficiary_id:
				res['partner_id'] = record.request_beneficiary_id.id
		return res

	def action_create_sale_order(self):
		self.ensure_one()
		value = []
		for data in self.new_order_line_ids:
			value.append([0, 0, {
				'product_id' : data.product_id.id,
				'name' : data.name,
				'product_uom_qty' : data.product_qty,
				'price_unit' : data.new_price_unit,
			}])
		res = self.env['sale.order'].create({
			'partner_id': self.partner_id.id,
			'date_order': self.date_order,
			'order_line': value,
			'request_purchase': self.request_purchase,
			'transport_request_id': self.transport_request_id.id or False,
		})
		return res


class getpurchaseorder(models.TransientModel):
	_inherit = 'getpurchase.orderdata'

	new_price_unit = fields.Float(
		string="New Unit Price", store=True, readonly=False, required=True,
		compute='_compute_new_price_unit')

	@api.depends(
		'price_unit', 'new_order_line_id.partner_id',
		'new_order_line_id.request_purchase')
	def _compute_new_price_unit(self):
		for line in self:
			new_price_unit = line.price_unit
			if line.new_order_line_id.request_purchase and \
				line.new_order_line_id.partner_id.gain_margin:
				gain_margin = line.new_order_line_id.partner_id.gain_margin
				new_price_unit += (line.price_unit * gain_margin / 100)
			line.new_price_unit = new_price_unit

	@api.depends('product_qty', 'new_price_unit')
	def _compute_total(self):
		for record in self:
			record.product_subtotal = record.product_qty * record.new_price_unit
