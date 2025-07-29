""" Partner """
from odoo import fields, models


class ResPartner(models.Model):
    """ Inherit Res Partner """

    _inherit = 'res.partner'

    contact_type_id = fields.Many2one("contact.type", string="Tipo de Contacto")
    contact_type_name = fields.Char(related="contact_type_id.name")
    contact_number = fields.Char("Número de Aduana")
    custom_section = fields.Char("Sección de Aduana")
    custom_numenclature = fields.Char("Nomenclatura de Aduana")
    custom_broker_ids = fields.Many2many(
        "res.partner", "partner_custom_broker_rel", "partner_id", "custom_broker_id",
        string="Corresponsales")
    related_custom_ids = fields.Many2many(
        "res.partner", "partner_related_custom_rel", "partner_id", "related_custom_id",
        string="Aduanas Relacionadas")
    custom_house_ids = fields.Many2many(
        'custom.house', 'custom_house_res_partner_rel',
        'partner_id', 'custom_house_id', string='Aduanas')