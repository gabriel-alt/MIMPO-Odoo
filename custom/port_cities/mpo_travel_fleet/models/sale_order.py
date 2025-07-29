"""Sale order"""
from odoo import models, fields, api, _
from odoo.osv import expression

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    trip_needed = fields.Boolean()
    trip_number = fields.Char(readonly=True, copy=False)
    trip_vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Economic',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    trip_driver_id = fields.Many2one(
        'res.partner', 'Operator', readonly=True,
        related='trip_vehicle_id.driver_id')
    trip_tow_ids = fields.Many2many(
        'fleet.vehicle', 'sale_order_trip_tow_rel',
        'sale_id', 'tow_id', 'Trailer',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    trip_origin_id = fields.Many2one(
        'res.partner', 'Origen')
    trip_destiny_id = fields.Many2one(
        'res.partner', 'Destination')
    trip_tag_ids = fields.Many2many(
        'fleet.vehicle.tag', 'sale_order_vehicle_tag_rel',
        'sale_id', 'tag_id', 'Vehicle Tag', readonly=True,
        related='trip_vehicle_id.tag_ids')
    trip_dolly_id = fields.Many2one(
        'fleet.vehicle', 'Dolly',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    trip_chassis_id = fields.Many2one(
        'fleet.vehicle', 'Chassis 1',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    trip_chassis2_id = fields.Many2one(
        'fleet.vehicle', 'Chassis 2',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    departure_date = fields.Datetime(string='Date and time of Departure')
    arrive_date = fields.Datetime(string='Date and time of Arrival')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company_id = vals.get(
                'company_id', self.default_get(['company_id'])['company_id'])
            self_comp = self.with_company(company_id)
            if vals.get('trip_needed'):
                vals['trip_number'] = self_comp.env['ir.sequence'].next_by_code(
                    'sale.trip.number') or '/'
        return super(SaleOrder, self).create(vals_list)

    def write(self, vals):
        if vals.get('trip_needed'):
            for this in self:
                if not vals.get('trip_number') and not this.trip_number:
                    vals['trip_number'] = self.env['ir.sequence'].next_by_code(
                        'sale.trip.number') or '/'
        return super(SaleOrder, self).write(vals)

    @api.model
    def _name_search(self, name, args=None, operator='ilike',
                     limit=100, name_get_uid=None):
        if not self.env.context.get('show_trip_number'):
            return super()._name_search(
                name, args=args, operator=operator,
                limit=limit, name_get_uid=name_get_uid)
        args = args or []
        domain = []
        if name:
            if operator in ('=', '!='):
                domain = [
                    '|', ('trip_number', '=', name.split(' ')[0]),
                    ('name', operator, name)]
            else:
                domain = [
                    '|', ('trip_number', '=ilike', name.split(' ')[0] + '%'),
                    ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        return self._search(expression.AND(
            [domain, args]), limit=limit, access_rights_uid=name_get_uid)

    def name_get(self):
        if not self.env.context.get('show_trip_number') and \
            self.env.context.get('default_move_type') != 'in_invoice':
            return super().name_get()
        result = []
        for trip in self:
            name = trip.trip_number or trip.name
            result.append((trip.id, name))
        return result
