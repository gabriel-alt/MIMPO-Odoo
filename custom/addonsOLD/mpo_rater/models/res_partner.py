# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_customs_house = fields.Boolean(string='Es aduana?')
    custom_house_ref = fields.Float(string='Código aduana')

    @api.onchange('contact_type_id')
    def onchange_contact_type_id(self):
        aduana = self.env.ref('mpo_contact_type.data_contact_type_custom')
        corresponsal = self.env.ref('mpo_contact_type.data_contact_type_custom_broker')
        for rec in self:
            if rec.contact_type_id and rec.contact_type_id.id == aduana.id:
                rec.is_customs_house = True
            elif rec.contact_type_id and rec.contact_type_id.id == corresponsal.id:
                rec.is_customs_house = False
