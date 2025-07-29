""" Account Move """
from odoo import fields, models


class AccountMove(models.Model):
    """ Inherit Account Move """

    _inherit = 'account.move'

    def contact_type_domain(self):
        return [('contact_type_id','=',self.env.ref('mpo_contact_type.data_contact_type_custom_broker').id)]

    custom_broker_id = fields.Many2one("res.partner", string="Corresponsal", domain=contact_type_domain)


class AccountMoveLine(models.Model):
    """ Inherit Account Move Line """

    _inherit = 'account.move.line'

    custom_broker_id = fields.Many2one("res.partner", string="Corresponsal")
