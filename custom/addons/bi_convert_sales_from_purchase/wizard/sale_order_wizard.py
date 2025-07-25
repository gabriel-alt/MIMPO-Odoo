# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from odoo import api, fields, models, _
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class createsaleorder(models.TransientModel):
	_name = 'create.saleorder'
	_description = "Create Sale Order"


	new_order_line_ids = fields.One2many( 'getpurchase.orderdata', 'new_order_line_id', string="Order Line")
	
	partner_id = fields.Many2one('res.partner', string='Customer', required=True)
	date_order = fields.Datetime(string='Order Date', required=True, default=fields.Datetime.now)
	


	@api.model
	def default_get(self,  default_fields):
		res = super(createsaleorder, self).default_get(default_fields)
		record = self.env['purchase.order'].browse(self._context.get('active_ids',[]))
		update = []
		for record in record.order_line:
			update.append((0,0,{
					'product_id' : record.product_id.id,
					'name' : record.name,
					'product_qty' : record.product_qty,
					'price_unit' : record.price_unit,
					'product_subtotal' : record.price_subtotal,
					'date_planned' : datetime.today(),
				}))

			res.update({'new_order_line_ids':update})
		return res	



	def action_create_sale_order(self):
		self.ensure_one()
		res = self.env['sale.order'].browse(self._context.get('id',[]))
		value = [] 
		for data in self.new_order_line_ids:
			value.append([0,0,{
								'product_id' : data.product_id.id,
								'name' : data.name,
								'product_uom_qty' : data.product_qty,
								'price_unit' : data.price_unit,
								}])
		res.create({	'partner_id' : self.partner_id.id,
						'date_order' : self.date_order,
						'order_line':value,
						
					})
		return 



class getpurchaseorder(models.TransientModel):
	_name = 'getpurchase.orderdata'
	_description = "Get purchase Order Data"


	new_order_line_id = fields.Many2one('create.saleorder')
	
	product_id = fields.Many2one('product.product', string="Product", required=True)
	name = fields.Char(string="Description", required=True)
	product_qty = fields.Float(string='Quantity', required=True)
	price_unit = fields.Float(string="Unit Price", required = True)
	product_subtotal = fields.Float(string="Sub Total", compute='_compute_total')
	date_planned = fields.Datetime(string='Receipt Date')


	@api.depends('product_qty', 'price_unit')
	def _compute_total(self):
		for record in self:
			record.product_subtotal = record.product_qty * record.price_unit

