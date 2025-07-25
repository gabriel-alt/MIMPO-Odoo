# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_service = fields.Boolean()
    service_description = fields.Char()
    service_type_id = fields.Many2one('fleet.service.type')
    service_date = fields.Date()
    vehicle_id = fields.Many2one('fleet.vehicle')
    driver_id = fields.Many2one('res.partner')
    odometer = fields.Float(string='Odometer Value')

    def prepare_vals_vehicle_log_service(self):
        """function for prepare vals of vehicle log service"""
        self.ensure_one()
        return {
            'description': self.service_description,
            'service_type_id': self.service_type_id.id,
            'date': self.service_date,
            'vendor_id': self.partner_id.id,
            'vehicle_id': self.vehicle_id and self.vehicle_id.id or False,
            'purchaser_id': self.driver_id and self.driver_id.id or False,
            'odometer': self.odometer,
            'vendor_bill_id': self.id,
            'amount': self.amount_total,
        }

    def _generate_vehicle_log_service(self):
        """function for generate vehicle log service"""
        self.ensure_one()
        log_vals = self.prepare_vals_vehicle_log_service()
        log_id = self.env['fleet.vehicle.log.services'].create(log_vals)
        return log_id

    def _post(self, soft=True):
        # OVERRIDE
        # For generates the service log in the services model
        posted = super()._post(soft)
        for bill in posted.filtered(
            lambda m: m.move_type == 'in_invoice' and \
                m.is_service and m.service_type_id and \
                m.service_type_id.create_log_bill):
            bill._generate_vehicle_log_service()
        return posted
