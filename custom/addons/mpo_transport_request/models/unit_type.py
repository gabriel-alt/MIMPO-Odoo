from odoo import fields, models


class UnitType(models.Model):
    _name = "unit.type"
    _description = "Types of external fleet units"

    name = fields.Char(string="Unit Type")
