from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    trip_number_invoice_id = fields.Many2one(
        'sale.order', check_company=True, string='Trip Number',
        domain=[('trip_needed', '=', True), ('trip_number', '!=', False)],
        context={'show_trip_number': True})

    def _where_calc(self, domain, active_test=True):
        for dom in domain:
            if isinstance(dom, list) and len(dom) == 3 and \
                'trip_number_invoice_id' in dom[0] and isinstance(dom[2], str):
                dom[0] = 'trip_number_invoice_id.trip_number'
        return super()._where_calc(domain, active_test)
