""" Res Partner """
from odoo import models, fields

class ResPartner(models.Model):
    """ Inherit Res Partner """
    _inherit = 'res.partner'

    def _display_address_mx(self):
        self.ensure_one()
        res = ''
        if self.street_name or self.street_number or self.street_number2:
            street = self.street_name
            if self.street_number or self.street_number2:
                if street:
                    street += ', '
                street += 'Num. '
            if self.street_number:
                street += 'Ext. ' + self.street_number
            if self.street_number2:
                if not self.street_number:
                    street += ', '
                street += 'Int. ' + self.street_number2
            res = 'DOMICILIO: ' + street
        if self.l10n_mx_edi_colony or self.zip:
            if res:
                res += '<br/>'
            colony = self.l10n_mx_edi_colony
            if self.zip:
                if colony:
                    colony += ', '
                colony += 'C.P. ' + self.zip
            res += 'COLONIA: ' + colony
        if self.l10n_mx_edi_locality_id or self.city_id or \
            self.state_id or self.country_id:
            if res:
                res += '<br/>'
            country = self.l10n_mx_edi_locality_id.name
            if self.city_id:
                if country:
                    country += ', '
                country += self.city_id.name
            if self.state_id:
                if country:
                    country += ', '
                country += self.state_id.name
            if self.country_id:
                if country:
                    country += ', '
                country += self.country_id.name
            res += 'CIUDAD/EDO: ' + country
        if self.vat:
            if res:
                res += '<br/>'
            res += 'R.F.C: ' + self.vat
        return res
