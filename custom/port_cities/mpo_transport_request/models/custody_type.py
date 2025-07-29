from odoo import fields, models


class CustodyType(models.Model):
    _name = "custody.type"
    _description = "Types of Custody"

    name = fields.Char(string="Custodial Name")
