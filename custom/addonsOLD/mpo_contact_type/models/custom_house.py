""" Aduana """
from odoo import fields, models


class CustomHouse(models.Model):
    """ Define Aduana """
    _name = 'custom.house'
    _description = 'Aduana'
    _order = 'name'

    name = fields.Char('Aduanas Name', required=True)
    number = fields.Char('Aduanas Number')
    section = fields.Char('Aduanas Section')
