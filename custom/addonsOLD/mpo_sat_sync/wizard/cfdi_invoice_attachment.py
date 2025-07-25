'''cfdi.invoice.attachment'''
from odoo import models, _
import base64
import json, xmltodict
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError

from odoo.addons.l10n_mx_sat_sync_itadmin_ee.models.special_dict import CaselessDictionary
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.parser import parse

def convert_to_special_dict(d):
    for k, v in d.items():
        if isinstance(v, dict):
            d.__setitem__(k, convert_to_special_dict(CaselessDictionary(v)))
        else:
            d.__setitem__(k, v)
    return d
    
class CfdiInvoiceAttachment(models.TransientModel):
    '''inherit cfdi.invoice.attachment'''

    _inherit = 'cfdi.invoice.attachment'

    def import_supplier_invoice(self, file_content, journal=False):
        ''' replace to add set to_agency'''
        file_content = base64.b64decode(file_content)
        file_content = file_content.replace(b'cfdi:', b'')
        file_content = file_content.replace(b'tfd:', b'')
        try:
            data = json.dumps(xmltodict.parse(file_content))  # ,force_list=('Concepto','Traslado',)
            data = json.loads(data)
        except Exception as e:
            data = {}
            raise UserError(str(e))

        data = CaselessDictionary(data)
        data = convert_to_special_dict(data)

        invoice_obj = self.env['account.move']
        invoice_line_obj = self.env['account.move.line']
        vendor_data = data.get('Comprobante', {}).get('Emisor', {})
        invoice_line_data = data.get('Comprobante', {}).get('Conceptos', {}).get('Concepto', [])
        if type(invoice_line_data) != list:
            invoice_line_data = [invoice_line_data]

        invoice_date = data.get('Comprobante', {}).get('@Fecha')
        vendor_reference = data.get('Comprobante', {}).get('@Serie', '') + data.get('Comprobante', {}).get('@Folio', '')
        receptor_data = data.get('Comprobante', {}).get('Receptor', {})
        timbrado_data = data.get('Comprobante', {}).get('Complemento', {}).get('TimbreFiscalDigital', {})

        vendor_uuid = timbrado_data.get('@UUID')

        if vendor_uuid != '':
            vendor_order_exist = invoice_obj.search([('l10n_mx_edi_cfdi_uuid_cusom','=',vendor_uuid.lower())],limit=1)
            if not vendor_order_exist:
                vendor_order_exist = invoice_obj.search([('l10n_mx_edi_cfdi_uuid_cusom','=',vendor_uuid.upper())],limit=1)
            if vendor_order_exist:
                raise UserError("Factura ya existente con ese UUID %s" % (vendor_uuid))

        if vendor_reference != '':
            invoice_exist = invoice_obj.search([('ref','=',vendor_reference), ('move_type','=', 'in_invoice')],limit=1)
            if invoice_exist:
                vendor_reference = ''

        vendor = self.create_update_partner(vendor_data, is_customer=False, is_supplier=True)

        ctx = self._context.copy()
        ctx.update({'default_type': 'in_invoice', 'move_type': 'in_invoice'})
        if not journal:
            journal = invoice_obj.with_context(ctx)._default_journal()

        rfc_company_id = self.env['res.company'].search([
            ('vat', '=', receptor_data.get('@Rfc')),
            ('name', '=', receptor_data.get('@Nombre'))], 
            limit=1)
        to_agency = False
        if self.env.company == rfc_company_id:
            to_agency = True

        invoice_vals = {
            'move_type':'in_invoice',
            'partner_id':vendor.id,
            'ref':vendor_reference,
            'l10n_mx_edi_usage' : receptor_data.get('@UsoCFDI') if receptor_data.get('@UsoCFDI') != 'S01' else 'P01',
            'l10n_mx_edi_payment_method_id': self.env['l10n_mx_edi.payment.method'].sudo().search([('code','=',data.get('Comprobante', {}).get('@FormaPago', {}))]),
            'l10n_mx_edi_payment_policy':data.get('Comprobante',{}).get('@MetodoPago',{}),
            'currency_id' : journal.currency_id.id or journal.company_id.currency_id.id or self.env.company.currency_id.id,
            'company_id' : self.env.company.id,
            'journal_id' : journal.id,
            'to_agency': to_agency,
            'client_id': vendor.id if vendor else False,
            'rfc_client': vendor_data.get('@Rfc')
        }

        currency_code = data.get('Comprobante', {}).get('@Moneda', 'MXN')
        currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
        if not currency:
            currency = self.env['res.currency'].with_context(active_test=False).search([('name','=',currency_code)], limit=1)
            if currency:
                currency.write({'active': True})
        if currency:
            invoice_vals.update({'currency_id': currency.id})

        vendor_invoice = invoice_obj.with_context(ctx).new(invoice_vals)
        vendor_invoice._onchange_partner_id()
        invoice_vals = vendor_invoice._convert_to_write({name: vendor_invoice[name] for name in vendor_invoice._cache})
        invoice_vals.update({'invoice_date':parse(invoice_date).strftime(DEFAULT_SERVER_DATE_FORMAT),'journal_id' : journal.id,})

        fields = invoice_line_obj._fields.keys()
        ctx.update({'journal': journal.id})

        move_lines = []

        for line in invoice_line_data:
            product_name = line.get('@Descripcion')
            discount_amount = safe_eval(line.get('@Descuento', '0.0'))
            unit_price = safe_eval(line.get('@ValorUnitario', '0.0'))
            default_code = line.get('@NoIdentificacion')
            qty = safe_eval(line.get('@Cantidad', '1.0'))
            clave_unidad = line.get('@ClaveUnidad')
            clave_producto = line.get('@ClaveProdServ')
            taxes = line.get('Impuestos', {}).get('Traslados', {}).get('Traslado')
            tax_ids  = []
            if taxes:
                if type(taxes) != list:
                    taxes = [taxes]
            else:
                taxes = []
            no_imp_tras = len(taxes)
            if line.get('Impuestos',{}).get('Retenciones',{}):
                other_taxes = line.get('Impuestos',{}).get('Retenciones',{}).get('Retencion')
                if type(other_taxes)!=list:
                    other_taxes = [other_taxes]
                    
                taxes.extend(other_taxes)
            if taxes:
                if type(taxes)!=list:
                    taxes = [taxes]
                tax_ids  = self.get_tax_from_codes(taxes,'purchase',no_imp_tras)
            
            product_exist = self.get_or_create_product(default_code, product_name, clave_unidad, unit_price, clave_producto, sale_ok=False, purchase_ok=True)

            if discount_amount:
                discount_percent = discount_amount * 100.0 / (unit_price * qty)
            else:
                discount_percent = 0.0

            line_data = invoice_line_obj.default_get(fields)
            line_data.update({
                'product_id': product_exist.id,
                'name': product_name,
                'product_uom_id': product_exist.uom_po_id.id,
                'price_unit': unit_price,
                'discount': discount_percent,
            })

            if taxes:
                line_data.update({
                    'tax_ids': [(6, 0, tax_ids)],
                    'quantity': qty or 1,
                    'price_unit': unit_price,
                })
            else:
                line_data.update({
                    'tax_ids': [],
                    'quantity': qty or 1,
                    'price_unit': unit_price,
                })
            move_lines.append((0, 0, line_data))

        if move_lines:
            invoice_vals.update({'invoice_line_ids': move_lines})
            if 'line_ids' in invoice_vals:
                invoice_vals.pop('line_ids')

        invoice_exist = invoice_obj.with_context(ctx).create(invoice_vals)
        # invoice_exist.compute_taxes()
        action = self.env.ref('account.action_move_in_invoice_type').sudo()
        result = action.read()[0]
        res = self.env.ref('account.view_move_form', False).sudo()
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = invoice_exist.id
        return result

