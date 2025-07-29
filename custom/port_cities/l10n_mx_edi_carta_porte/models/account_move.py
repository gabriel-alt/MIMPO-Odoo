# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from lxml import etree
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)

class CfdiTrasladoLine(models.Model):
    _name = "cp.traslado.line"
    
    cfdi_traslado_id= fields.Many2one(comodel_name='account.move',string="CFDI Traslado")
    product_id = fields.Many2one('product.product',string='Producto',required=True)
    name = fields.Text(string='Descripción',required=True,)
    quantity = fields.Float(string='Cantidad', digits=dp.get_precision('Unidad de medida del producto'),required=True, default=1)
    price_unit = fields.Float(string='Precio unitario', required=True, digits=dp.get_precision('Product Price'))
    invoice_line_tax_ids = fields.Many2many('account.tax',string='Taxes')
    currency_id = fields.Many2one('res.currency', related='cfdi_traslado_id.currency_id', store=True, related_sudo=False, readonly=False)
    price_subtotal = fields.Monetary(string='Subtotal',
        store=True, readonly=True, compute='_compute_price', help="Subtotal")
    price_total = fields.Monetary(string='Cantidad (con Impuestos)',
        store=True, readonly=True, compute='_compute_price', help="Cantidad total con impuestos")
    pesoenkg = fields.Float(string='Peso Kg', digits=dp.get_precision('Product Price'))
    pedimento = fields.Many2many('stock.lot', string='Pedimentos', copy=False)
    guiaid_numero = fields.Char(string=_('No. Guia'))
    guiaid_descrip = fields.Char(string=_('Descr. guia'))
    guiaid_peso = fields.Float(string='Peso guia')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        self.name = self.product_id.partner_ref
        company_id = self.env.user.company_id
        taxes = self.product_id.taxes_id.filtered(lambda r: r.company_id == company_id)
        self.invoice_line_tax_ids = fp_taxes = taxes
        fix_price = self.env['account.tax']._fix_tax_included_price
        self.price_unit = fix_price(self.product_id.lst_price, taxes, fp_taxes)
        self.pesoenkg = self.product_id.weight

    @api.depends('price_unit', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'cfdi_traslado_id.partner_id', 'cfdi_traslado_id.currency_id',)
    def _compute_price(self):
        for line in self:
            currency = line.cfdi_traslado_id and line.cfdi_traslado_id.currency_id or None
            price = line.price_unit
            taxes = False
            if line.invoice_line_tax_ids:
                taxes = line.invoice_line_tax_ids.compute_all(price, currency, line.quantity, product=line.product_id, partner=line.cfdi_traslado_id.partner_id)
            line.price_subtotal = taxes['total_excluded'] if taxes else line.quantity * price
            line.price_total = taxes['total_included'] if taxes else line.price_subtotal

    @api.onchange('quantity')
    def _onchange_quantity(self):
        self.pesoenkg = self.product_id.weight * self.quantity

class CCPUbicacionesLine(models.Model):
    _name = "cp.ubicaciones.line"
    
    cfdi_traslado_id= fields.Many2one(comodel_name='account.move',string="CFDI Traslado")
    tipoubicacion = fields.Selection(
        selection=[('Origen', 'Origen'), 
                   ('Destino', 'Destino'),],
        string=_('Tipo Ubicación'), required=True
    )
    contacto = fields.Many2one('res.partner',string="Remitente / Destinatario", required=True)
    numestacion = fields.Many2one('cve.estaciones',string='Número de estación')
    fecha = fields.Datetime(string=_('Fecha Salida / Llegada'), required=True)
    tipoestacion = fields.Many2one('cve.estacion',string='Tipo estación')
    distanciarecorrida = fields.Float(string='Distancia recorrida')
    tipo_transporte = fields.Selection(
        selection=[('01', 'Autotransporte'), 
                  # ('02', 'Marítimo'), 
                   ('03', 'Aereo'),
                   #('04', 'Ferroviario')
                  ],
        string=_('Tipo de transporte')
    )
    idubicacion = fields.Char(string=_('ID Ubicacion'))

class CCPRemolqueLine(models.Model):
    _name = "cp.remolques.line"

    cfdi_traslado_id= fields.Many2one(comodel_name='account.move',string="CFDI Traslado")
    subtipo_id = fields.Many2one('cve.remolque.semiremolque',string="Subtipo")
    placa = fields.Char(string=_('Placa'))

class CCPPropietariosLine(models.Model):
    _name = "cp.figura.line"

    cfdi_traslado_id= fields.Many2one(comodel_name='account.move',string="CFDI Traslado")
    figura_id = fields.Many2one('res.partner',string="Contacto")
    tipofigura = fields.Many2one('cve.figura.transporte',string="Tipo figura")
    partetransporte = fields.Many2many('cve.parte.transporte',string="Parte transporte")

class AccountMove(models.Model):
    _inherit = 'account.move'

    factura_line_ids = fields.One2many(comodel_name='cp.traslado.line', inverse_name='cfdi_traslado_id', string='CFDI Traslado Line', copy=True)
    tipo_transporte = fields.Selection(
        selection=[('01', 'Autotransporte'), 
                  # ('02', 'Marítimo'), 
                   ('03', 'Aereo'),
                  # ('04', 'Ferroviario')
                  ],
        string=_('Tipo de transporte'),required=True, default='01'
    )
    carta_porte = fields.Boolean('Agregar carta porte', default = False)

    ##### atributos CP 
    transpinternac = fields.Selection(
        selection=[('Sí', 'Si'), 
                   ('No', 'No'),],
        string=_('¿Es un transporte internacional?'),default='No',
    )
    entradasalidamerc = fields.Selection(
        selection=[('Entrada', 'Entrada'), 
                   ('Salida', 'Salida'),],
        string=_('¿Las mercancías ingresan o salen del territorio nacional?'),
    )
    viaentradasalida = fields.Many2one('cve.transporte',string='Vía de ingreso / salida')
    totaldistrec = fields.Float(string='Distancia recorrida')

    ##### ubicaciones CP
    ubicaciones_line_ids = fields.One2many(comodel_name='cp.ubicaciones.line', inverse_name='cfdi_traslado_id', string='Ubicaciones', copy=True)

    ##### mercancias CP
    pesobrutototal = fields.Float(string='Peso bruto total', compute='_compute_pesobruto')
    unidadpeso = fields.Many2one('cve.clave.unidad',string='Unidad peso')
    pesonetototal = fields.Float(string='Peso neto total')
    numerototalmercancias = fields.Float(string='Numero total de mercancías', compute='_compute_mercancia')
    cargoportasacion = fields.Float(string='Cargo por tasación')

    #transporte
    permisosct = fields.Many2one('cve.tipo.permiso',string='Permiso SCT')
    numpermisosct = fields.Char(string=_('Número de permiso SCT'))

    #autotransporte
    autotrasporte_ids = fields.Many2one('cp.autotransporte',string='Unidad')
    remolque_line_ids = fields.One2many(comodel_name='cp.remolques.line', inverse_name='cfdi_traslado_id', string='Remolque', copy=True)
    nombreaseg_merc = fields.Char(string=_('Nombre de la aseguradora'))
    numpoliza_merc = fields.Char(string=_('Número de póliza'))
    primaseguro_merc = fields.Float(string=_('Prima del seguro'))
    seguro_ambiente = fields.Char(string=_('Nombre aseguradora'))
    poliza_ambiente = fields.Char(string=_('Póliza no.'))

    ##### Aereo CP
    numeroguia = fields.Char(string=_('Número de guía'))
    lugarcontrato = fields.Char(string=_('Lugar de contrato'))
    matriculaaeronave = fields.Char(string=_('Matrícula Aeronave'))
    transportista_id = fields.Many2one('res.partner',string="Transportista")
    embarcador_id = fields.Many2one('res.partner',string="Embarcador")

    uuidcomercioext = fields.Char(string=_('UUID Comercio Exterior'))
    paisorigendestino = fields.Many2one('res.country', string='País Origen / Destino')

    # figura transporte
    figuratransporte_ids = fields.One2many(comodel_name='cp.figura.line', inverse_name='cfdi_traslado_id', string='Seguro mercancías', copy=True)

    @api.onchange('factura_line_ids')
    def _compute_pesobruto(self):
        for invoice in self:
           peso = 0
           if invoice.carta_porte:
              if invoice.factura_line_ids:
                  for line in invoice.factura_line_ids:
                     peso += line.pesoenkg
              invoice.pesobrutototal = peso
           else:
              invoice.pesobrutototal = peso

    @api.onchange('factura_line_ids')
    def _compute_mercancia(self):
        for invoice in self:
           cant = 0
           if invoice.carta_porte:
              if invoice.factura_line_ids:
                  for line in invoice.factura_line_ids:
                      cant += 1
              invoice.numerototalmercancias = cant
           else:
              invoice.numerototalmercancias = cant

    ### revisar si lo dejamos
    def _l10n_mx_edi_decode_cfdi(self, cfdi_data=None):
        # OVERRIDE

        def get_node(cfdi_node, attribute, namespaces):
            if hasattr(cfdi_node, 'Complemento'):
                node = cfdi_node.Complemento.xpath(attribute, namespaces=namespaces)
                return node[0] if node else None
            else:
                return None

        vals = super()._l10n_mx_edi_decode_cfdi(cfdi_data=cfdi_data)
        if vals.get('cfdi_node') is None:
            return vals

        cfdi_node = vals['cfdi_node']

#        external_trade_node = get_node(
#            cfdi_node,
##            'leyendasFisc:LeyendasFiscales[1]',
#            {'leyendasFisc': 'http://www.sat.gob.mx/leyendasFiscales'},
#        ) or {}

#        for char in external_trade_node.findall('{http://www.sat.gob.mx/leyendasFiscales}Leyenda'):
#            vals.update({
#               'disposicionFiscal': char.get('disposicionFiscal', ''),
#               'norma': char.get('norma', ''),
#               'textoLeyenda': char.get('textoLeyenda', ''),
#            })

        return vals
