# -*- coding: utf-8 -*-

from odoo import models, fields, api, http
from odoo.exceptions import ValidationError, UserError
import json
import requests
import logging
_logger = logging.getLogger(__name__)

reco_url = 'http://192.168.11.21:81/SIRServicesApi/api/Cliente/'
api_token = 'M1mp0S3rvic3s'

class PartnerLegalContact(models.Model):
    _name = 'partner.legal.contact'
    _descripcion = 'Legal Contact for Partner'
    
    legal_partner_id = fields.Many2one("res.partner", "Registro asociado", ondelete="restrict")
    name = fields.Many2one("res.partner", string="Representante legal", ondelete="cascade")
    legal_partner_rfc = fields.Char(string="RFC", related="name.vat", store=True)
    legal_partner_curp = fields.Char(string="CURP", related="name.l10n_mx_edi_curp", store=True)
    legal_partner_default = fields.Boolean(string="Por defecto")

    @api.onchange('name')
    def check_legal_partner(self):
        for record in self:
            if record.name:
                if not record.name.vat:
                    raise ValidationError("El registro seleccionado no tiene RFC establecido.")
                if not record.name.l10n_mx_edi_curp:
                    raise ValidationError("El registro seleccionado no tiene CURP establecido.")

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_supplier = fields.Boolean(string="Supplier")
    is_client = fields.Boolean(string="Client")
    firstname = fields.Char(string="Nombre")
    lastname = fields.Char(string="Apellido paterno")
    surname = fields.Char(string="Apellido materno")
    commercial_name = fields.Char(string="Nombre Comercial")
    type_company = fields.Selection([('fisica', 'Física'),
                                     ('moral', 'Moral'),], string="Tipo de empresa", default="moral")
    legal_partners_ids = fields.One2many('partner.legal.contact', 'legal_partner_id', string="Representantes legales")

    @api.onchange('zip')
    def _set_colony_code(self):
        self.l10n_mx_edi_colony_code = self.zip

    @api.onchange('legal_partners_ids')
    def set_default_legal_partner(self):
        for record in self:
            deafault_legal_count = 0
            for rec in record.legal_partners_ids:
                if rec.legal_partner_default:
                    deafault_legal_count += 1
            
            if deafault_legal_count > 1:
                raise ValidationError("Solo puede establecer a un solo Representante Legal por defecto")

    @api.onchange('lastname', 'surname', 'firstname')
    def onchange_names(self):
        for rec in self:
            if rec.firstname and rec.lastname and rec.surname:
                rec.name = rec.firstname + ' ' + rec.lastname + ' ' + rec.surname
            if not rec.firstname and rec.lastname and rec.surname:
                rec.name = rec.lastname + ' ' + rec.surname
            if rec.firstname and not rec.lastname and rec.surname:
                rec.name = rec.firstname + ' ' + rec.surname
            if rec.firstname and rec.lastname and not rec.surname:
                rec.name = rec.firstname + ' ' + rec.lastname
            if rec.firstname and not rec.lastname and not rec.surname:
                rec.name = rec.firstname
            if not rec.firstname and rec.lastname and not rec.surname:
                rec.name = rec.lastname
            if not rec.firstname and not rec.lastname and rec.surname:
                rec.name = rec.surname
            if not rec.firstname and not rec.lastname and not rec.surname:
                rec.name = ''

    def _prepare_url(self, rec_id):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        menu_id = str(self.env.ref('sale.sale_menu_root').id)
        action = str(self.env.ref('account.res_partner_action_customer').id)
        rec_id = str(rec_id)
        url = base_url + '/web#id=' + rec_id + '&' + 'menu_id=' + menu_id + '&cids=1&action=' + action + '&model=res.partner' + '&view_type=form'
        return url

    @api.model
    def default_get(self,  default_fields):
        res = super(ResPartner, self).default_get(default_fields)
        if self._context.get('default_customer_rank') or \
            self._context.get('res_partner_search_mode') == 'customer':
            res['is_client'] = True
        if self._context.get('default_supplier_rank') or \
            self._context.get('res_partner_search_mode') == 'supplier':
            res['is_supplier'] = True
        return res

    @api.model
    def create(self, vals):
        #_logger.warning(f"Valores (Create): {vals}")
        curp_representante_legal = ""
        rl_data = []
        if vals.get('is_supplier') and not vals.get('supplier_rank'):
            vals['supplier_rank'] = 1
        if vals.get('is_client') and not vals.get('customer_rank'):
            vals['customer_rank'] = 1

        if vals.get('company_type') == 'company':
            legal_partner_found = False
            legal_partner_id = False
            # if len(vals.get('legal_partners_ids')) < 1:
            #     raise ValidationError(("Debe existir al menos un represntante legal cuando se trate de una Empresa física o moral"))
            # else:
            if vals.get('legal_partners_ids', False):
                for lp in vals.get('legal_partners_ids'):
                    if lp[2].get('legal_partner_default'):
                        legal_partner_id = int(lp[2].get('name'))
                        legal_partner_found = True
                        break

            # if not legal_partner_found:
            #     raise ValidationError(("Al menos un representante legal debe estar marcado como representante por defecto."))
            if legal_partner_id:
                rl = self.env['res.partner'].search([('id', '=', legal_partner_id)])
                
                for rlegal in vals.get('legal_partners_ids'):
                    rl = self.env['res.partner'].search([('id', '=', int(rlegal[2].get('name')))])
                    rl_data.append({'Nombre': rl.name,
                                    'RFC': rl.vat,
                                    'CURP': rl.l10n_mx_edi_curp,
                                    'Default': rlegal[2].get('legal_partner_default')})
                _logger.warning(f"Representante legal data: {rl_data}")

                curp_representante_legal = rl.l10n_mx_edi_curp
        
        self = self.with_context(from_create=True)
        res = super(ResPartner, self).create(vals)
        ctx = self._context
        if ctx.get('res_partner_search_mode', False) and ctx.get('res_partner_search_mode', False) == 'customer':
            state = vals.get('state_id', False)
            if state:
                state = self.env['res.country.state'].browse(state)
            country = vals.get('country_id', False)
            if country:
                country = self.env['res.country'].browse(country)
                
            reco_vals = {
                'ClvCliente': res.id,
                'RFC': vals.get('vat', False) or '',
                'CURP': curp_representante_legal if (vals.get('type_company') == 'moral' and vals.get('company_type') == 'company') else vals.get("l10n_mx_edi_curp", ""),
                'RazonSocial': vals.get('commercial_name', False) if (vals.get('commercial_name', False) and vals.get('type_company', False) == 'moral') else vals.get('name', False) or '',
                'NombreComercial': vals.get('name', False) or '',
                'Nombre': vals.get('firstname', False) or '',
                'Paterno': vals.get('lastname', False) or '',
                'Materno': vals.get('surname', False) or '',
                'Email': vals.get('email', False) or '',
                'Calle': vals.get('street_name', False) or '',
                'NumInt': vals.get('street_number2', False) or '',
                'NumExt': vals.get('street_number', False) or '',
                'CodigoPostal': vals.get('zip', False) or '',
                'Estado': state.code if state else '',
                'Ciudad': vals.get('city', False) or '',
                'Colonia': vals.get('l10n_mx_edi_colony', False) or '',
                'Pais': country.l10n_mx_edi_code if country else '',
                'UrlOdoo': self._prepare_url(res.id),
                'ClaveEmpresa': ''
            }

            if len(rl_data) > 0:
                reco_vals['Representantes'] = rl_data
            else:
                reco_vals['Representantes'] = None

            url = reco_url
            token = api_token
            headers = {
                'APIKey': 'M1mp0S3rvic3s',
                'Content-Type': 'application/json'
            }
            body = json.dumps(reco_vals)
            _logger.info('body (create): %s', str(body))
            #Add try exception like revuelta weighthing

            response = requests.post(url+'Create', headers=headers, data=body)
            _logger.info('response: %s', str(response))
            if response.status_code == 200:
               my_json = response.content.decode('utf8').replace("'", '"')
               data = json.loads(my_json)
               _logger.info('*'*10)
               _logger.info('Status 200: %s', str(data['Mensaje']))
               _logger.info('*'*10)
               res.partner_ref = str(data['Clave'])
            else:
                raise ValidationError(_('The certificate content is invalid.'))
            _logger.info('*'*10)
        return res

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if vals.get('is_supplier') or vals.get('is_client'):
            for this in self:
                rank_vals = {}
                if this.is_supplier and not this.supplier_rank:
                    rank_vals['supplier_rank'] = 1
                if this.is_client and not this.customer_rank:
                    rank_vals['customer_rank'] = 1
                if rank_vals:
                    this.write(rank_vals)
        ctx = self._context
        #_logger.warning(f"Context (write): {ctx}")

        if ctx.get('res_partner_search_mode', False) and ctx.get('res_partner_search_mode', False) == 'customer' and not ctx.get('from_create', False):
            curp_representante_legal = ""

            if self.company_type == 'company':
                legal_partner_found = False
                # if len(self.legal_partners_ids) < 1:
                #     raise ValidationError(("Debe existir al menos un representante legal cuando se trate de una Empresa física o moral"))
                # else:
                for lp in self.legal_partners_ids:
                    if lp.legal_partner_default:
                        legal_partner_found = True
                        curp_representante_legal = lp.legal_partner_curp
                        break

            #     if not legal_partner_found:
            #         raise ValidationError(("Al menos un representante legal debe estar marcado como representante por defecto."))

            state = self.state_id
            country = self.country_id
            curp = self.l10n_mx_edi_curp
            if self.type_company == 'moral' and self.company_type == 'company' and curp_representante_legal:
                curp = curp_representante_legal
            reco_vals = {
                'ClvCliente': self.id,
                'RFC': self.vat,
                'CURP': curp,
                'RazonSocial': self.name,
                'NombreComercial': self.name,
                'Nombre': self.firstname if self.firstname else '',
                'Paterno': self.lastname if self.lastname else '',
                'Materno': self.surname if self.surname else '',
                'Email': self.email if self.email else '',
                'Calle': self.street_name if self.street_name else '',
                'NumInt': self.street_number2 if self.street_number2 else '',
                'NumExt': self.street_number if self.street_number else '',
                'CodigoPostal': self.zip,
                'Estado': state.code if state else '',
                'Ciudad': self.city if self.city else '',
                'Colonia': self.l10n_mx_edi_colony if self.l10n_mx_edi_colony else '',
                'Pais': country.l10n_mx_edi_code if country else '',
                'ClaveEmpresa': ''
            }

            rl_data = []
            for rlegal in self.legal_partners_ids:
                rl_data.append({'Nombre': rlegal.name.name,
                                'RFC': rlegal.legal_partner_rfc,
                                'CURP': rlegal.legal_partner_curp,
                                'Default': rlegal.legal_partner_default})

            if len(rl_data) > 0:
                reco_vals['Representantes'] = rl_data
            else:
                reco_vals['Representantes'] = None

            url = reco_url
            token = api_token
            headers = {
                'APIKey': 'M1mp0S3rvic3s',
                'Content-Type': 'application/json'
            }
            body = json.dumps(reco_vals)
            _logger.info('body (write): %s', str(body))

            #Add try exception like revuelta weighthing
            response = requests.put(url+'Update', headers=headers, data=body)
            _logger.info('response: %s', str(response))
            _logger.info('response: %s', str(response.content))
            if response.status_code == 200:
               my_json = response.content.decode('utf8').replace("'", '"')
               data = json.loads(my_json)
               _logger.info('*'*10)
               _logger.info('Status 200: %s', str(data['Mensaje']))
               _logger.info('*'*10)

        return res

    def unlink(self):
        res = super(ResPartner, self).unlink()
        for rec in self:
            rec_id = str(rec.id)
            url = reco_url
            headers = {
                'APIKey': 'M1mp0S3rvic3s',
                'Content-Type': 'application/json'
            }
            response = requests.delete(url+'Delete?Clave='+rec_id, headers=headers)
            _logger.info('response: %s', str(response))
            if response.status_code == 200:
               _logger.info('*'*10)
               _logger.info('Status 200: %s', str(response.content))
               _logger.info('*'*10)

            return res
