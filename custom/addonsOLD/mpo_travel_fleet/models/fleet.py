"""Extend Fleet"""
from odoo import fields, models, api


class FleetVehicleState(models.Model):
    """extend fleet state"""
    _inherit = 'fleet.vehicle.state'

    state_category = fields.Selection([
        ('available', 'Available'), ('assigned', 'Assigned'),
        ('traveling', 'Traveling'), ('service', 'In service')
    ])

class FleetVehicle(models.Model):
    """extend fleet vehicle"""
    _inherit = 'fleet.vehicle'

    def _get_default_state(self):
        state = super(FleetVehicle, self)._get_default_state()
        if not state or state.state_category != 'available':
            state = self.env['fleet.vehicle.state'].search([
                ('state_category', '=', 'available')], limit=1)
        return state

    state_id = fields.Many2one(default=_get_default_state)
    state_category = fields.Selection(
        related='state_id.state_category', readonly=True, store=True)
