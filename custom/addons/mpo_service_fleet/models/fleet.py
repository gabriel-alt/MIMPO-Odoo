"""Extend Fleet"""
from odoo import fields, models, api

class FleetServiceType(models.Model):
    """extend fleet.service.type"""
    _inherit = 'fleet.service.type'

    create_log_bill = fields.Boolean('Create Log From Bill')

class FleetVehicleLogServices(models.Model):
    """extend fleet.vehicle.log.services"""
    _inherit = 'fleet.vehicle.log.services'

    vendor_bill_id = fields.Many2one(
        'account.move', readonly=True, copy=False)
