""" Contact Type """
from odoo import fields, models


class ContactType(models.Model):
    """ Define Contact Type """

    _name = 'contact.type'
    _description = 'Type of Contact'
    _order = 'name'

    name = fields.Char()
