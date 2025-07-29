# -*- coding: utf-8 -*-
from odoo import models, fields, _
import pytz
from odoo import tools
import logging
_logger = logging.getLogger(__name__)

class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_mx_edi_get_invoice_cfdi_values(self, invoice):
      # OVERRIDE
      vals = super()._l10n_mx_edi_get_invoice_cfdi_values(invoice)

      # External Trade
      if invoice.carta_porte:

        invoice.totaldistrec = 0

        cp_ubicacion = []
        for ubicacion in invoice.ubicaciones_line_ids:

            #corregir hora
            timezone = invoice._context.get('tz')
            if not timezone:
               timezone = invoice.env.user.partner_id.tz or 'America/Mexico_City'
            local = pytz.timezone(timezone)
            local_dt_from = ubicacion.fecha.replace(tzinfo=pytz.UTC).astimezone(local)
            date_fecha = local_dt_from.strftime ("%Y-%m-%dT%H:%M:%S")
            invoice.totaldistrec += float(ubicacion.distanciarecorrida)
            _logger.info('totaldistrec %s', invoice.totaldistrec)

            cp_ubicacion.append({
                            'TipoUbicacion': ubicacion.tipoubicacion,
                          # 'IDUbicacion': ubicacion.origen_id,
                            'RFCRemitenteDestinatario': ubicacion.contacto.vat,
                            'NombreRemitenteDestinatario': ubicacion.contacto.name,
                            'NumRegIdTrib': ubicacion.contacto.vat if ubicacion.contacto.country_id.l10n_mx_edi_code != 'MEX' else '',
                            'ResidenciaFiscal': ubicacion.contacto.country_id.l10n_mx_edi_code if ubicacion.contacto.country_id.l10n_mx_edi_code != 'MEX' else '',
                            'NumEstacion': invoice.tipo_transporte != '01' and ubicacion.numestacion.clave_identificacion or '',
                            'NombreEstacion': invoice.tipo_transporte != '01' and ubicacion.numestacion.descripcion or '',
                          # 'NavegacionTrafico': invoice.company_id.zip,
                            'FechaHoraSalidaLlegada': date_fecha,
                            'TipoEstacion': invoice.tipo_transporte != '01' and ubicacion.tipoestacion.c_estacion or '',
                            'DistanciaRecorrida': ubicacion.distanciarecorrida > 0 and ubicacion.distanciarecorrida or '',
                            'Domicilio': {
                                'Calle': ubicacion.contacto.street_name,
                                'NumeroExterior': ubicacion.contacto.street_number,
                                'NumeroInterior': ubicacion.contacto.street_number2,
                                'Colonia': ubicacion.contacto.l10n_mx_edi_colony_code if ubicacion.contacto.country_id.l10n_mx_edi_code == 'MEX' else ubicacion.contacto.l10n_mx_edi_colony or '',
                                'Localidad': ubicacion.contacto.l10n_mx_edi_locality_id.code if ubicacion.contacto.country_id.l10n_mx_edi_code == 'MEX' else ubicacion.contacto.l10n_mx_edi_locality,
                          #      'Referencia': self.company_id.cce_clave_estado.c_estado,
                                'Municipio': ubicacion.contacto.city_id.l10n_mx_edi_code if ubicacion.contacto.country_id.l10n_mx_edi_code == 'MEX' else ubicacion.contacto.city,
                                'Estado': ubicacion.contacto.state_id.code if ubicacion.contacto.country_id.l10n_mx_edi_code in ('MEX', 'USA', 'CAN') or ubicacion.contacto.state_id.code else 'NA',
                                'Pais': ubicacion.contacto.country_id.l10n_mx_edi_code,
                                'CodigoPostal': ubicacion.contacto.zip,
                            },
                         })

        #################  Atributos y Ubicacion ############################
   #     if self.tipo_transporte == '01' or self.tipo_transporte == '04':
        cartaporte20= {'TranspInternac': invoice.transpinternac,
                       'EntradaSalidaMerc': invoice.entradasalidamerc,
                       'ViaEntradaSalida': invoice.viaentradasalida.c_transporte,
                       'TotalDistRec': invoice.tipo_transporte == '01' and invoice.totaldistrec or '',
                       'PaisOrigenDestino': invoice.paisorigendestino.l10n_mx_edi_code,
                      }
  #      else:
  #          res.update({
  #                   'cartaporte': {
  #                          'TranspInternac': invoice.transpinternac,
  #                          'EntradaSalidaMerc': invoice.entradasalidamerc,
  #                          'ViaEntradaSalida': invoice.viaentradasalida.c_transporte,
  #                          'TipoTransporte': invoice.tipo_transporte,
  #                   },
  #              })

        cartaporte20.update({'Ubicaciones': cp_ubicacion})

        #################  Mercancias ############################
        mercancias = { 
                       'PesoBrutoTotal': invoice.pesobrutototal, #solo si es aereo o ferroviario
                       'UnidadPeso': invoice.unidadpeso.clave,
                       'PesoNetoTotal': invoice.pesonetototal if invoice.pesonetototal > 0 else '',
                       'NumTotalMercancias': int(invoice.numerototalmercancias),
                       'CargoPorTasacion': invoice.cargoportasacion if invoice.cargoportasacion > 0 else '',
        }

        mercancia = []
        for line in invoice.factura_line_ids:
            if line.quantity <= 0:
                continue
            mercancia_atributos = {
                            'BienesTransp': line.product_id.unspsc_code_id.code,
                            'ClaveSTCC': line.product_id.clave_stcc,
                            'Descripcion': self.clean_text(line.product_id.name),
                            'Cantidad': line.quantity,
                            'ClaveUnidad': line.product_id.uom_id.unspsc_code_id.code,
                            'Unidad': line.product_id.uom_id.name,
                            'Dimensiones': line.product_id.dimensiones or '',
                            'MaterialPeligroso': line.product_id.materialpeligroso or '',
                            'CveMaterialPeligroso': line.product_id.clavematpeligroso.clave or '',
                            'Embalaje': line.product_id.embalaje.clave or '',
                            'DescripEmbalaje': line.product_id.desc_embalaje or '',
                            'PesoEnKg': line.pesoenkg,
                            'ValorMercancia': line.price_subtotal,
                            'Moneda': invoice.currency_id.name,
                            'FraccionArancelaria': line.product_id.l10n_mx_edi_tariff_fraction_id.code if invoice.transpinternac == 'Sí' else '',
                            'UUIDComercioExt': invoice.uuidcomercioext,
            }
            pedimentos = []
            if line.pedimento:
               for no_pedimento in line.pedimento:
                  pedimentos.append({
                                 'Pedimento': no_pedimento.name[:2] + '  ' + no_pedimento.name[2:4] + '  ' + no_pedimento.name[4:8] + '  ' + no_pedimento.name[8:],
                  })
            guias = [] # soo si tiene un dato
            if line.guiaid_numero:
               guias.append({
                          'NumeroGuiaIdentificacion': line.guiaid_numero,
                          'DescripGuiaIdentificacion': line.guiaid_descrip,
                          'PesoGuiaIdentificacion': line.guiaid_peso,
               })

        #################  CantidadTransporta ############################
        #################  pueden haber varios revisar ############################
   #     mercancia_cantidadt = {
   #                         'Cantidad': merc.product_id.code,
   #                         'IDOrigen': merc.fraccionarancelaria.c_fraccionarancelaria,
   #                         'IDDestino': merc.cantidadaduana,
   #                       #  'CvesTransporte': merc.valorunitarioaduana,
   #     })
		
        #################  DetalleMercancia ############################
      #  mercancia_detalle = {
      #                      'UnidadPesoMerc': merc.product_id.code,
      #                      'PesoBruto': merc.fraccionarancelaria.c_fraccionarancelaria,
      #                      'PesoNeto': merc.cantidadaduana,
      #                      'PesoTara': merc.valorunitarioaduana,
      #                      'NumPiezas': merc.valordolares,
      #  }


#           mercancia.update({'mercancia_cantidadt': mercancia_cantidadt})
#           mercancia.update({'mercancia_detalle': mercancia_detalle})
            mercancia.append({'atributos': mercancia_atributos, 'Pedimentos': pedimentos, 'GuiasIdentificacion': guias})
        mercancias.update({'mercancia': mercancia})

        if invoice.tipo_transporte == '01': #autotransporte
              transpote_detalle = {
                            'PermSCT': invoice.permisosct.clave,
                            'NumPermisoSCT': invoice.numpermisosct,
                            'IdentificacionVehicular': {
                                 'ConfigVehicular': invoice.autotrasporte_ids.confvehicular.clave,
                                 'PlacaVM': invoice.autotrasporte_ids.placavm,
                                 'AnioModeloVM': invoice.autotrasporte_ids.aniomodelo,
                            },
                            'Seguros': {
                                 'AseguraRespCivil': invoice.autotrasporte_ids.nombreaseg,
                                 'PolizaRespCivil': invoice.autotrasporte_ids.numpoliza,
                                 'AseguraCarga': invoice.nombreaseg_merc,
                                 'PolizaCarga': invoice.numpoliza_merc,
                                 'PrimaSeguro': invoice.primaseguro_merc,
                                 'AseguraMedAmbiente': invoice.seguro_ambiente,
                                 'PolizaMedAmbiente': invoice.poliza_ambiente,
                            },
              }
              remolques = []
              if invoice.remolque_line_ids:
                 for remolque in invoice.remolque_line_ids:
                     remolques.append({
                            'SubTipoRem': remolque.subtipo_id.clave,
                            'Placa': remolque.placa,
                     })
                 transpote_detalle.update({'Remolques': remolques})

              mercancias.update({'Autotransporte': transpote_detalle})
        elif invoice.tipo_transporte == '02': # maritimo
              maritimo = []
        elif invoice.tipo_transporte == '03': #aereo
              transpote_detalle = {
                            'PermSCT': invoice.permisosct.clave,
                            'NumPermisoSCT': invoice.numpermisosct,
                            'MatriculaAeronave': invoice.matriculaaeronave,
                         #   'NombreAseg': invoice.nombreaseg,  ******
                         #   'NumPolizaSeguro': invoice.numpoliza, *****
                            'NumeroGuia': invoice.numeroguia,
                            'LugarContrato': invoice.lugarcontrato,
                            'CodigoTransportista': invoice.transportista_id.codigotransportista.clave,
                            'RFCEmbarcador': invoice.embarcador_id.vat if invoice.embarcador_id.country_id.l10n_mx_edi_code == 'MEX' else '',
                            'NumRegIdTribEmbarc': invoice.embarcador_id.vat if invoice.embarcador_id.country_id.l10n_mx_edi_code != 'MEX' else '',
                            'ResidenciaFiscalEmbarc': invoice.embarcador_id.country_id.l10n_mx_edi_code if invoice.embarcador_id.country_id.l10n_mx_edi_code != 'MEX' else '',
                            'NombreEmbarcador': invoice.embarcador_id.name,
              }
              mercancias.update({'TransporteAereo': transpote_detalle})
        elif invoice.tipo_transporte == '04': #ferroviario
              ferroviario = []

        cartaporte20.update({'Mercancias': mercancias})

        #################  Figura transporte ############################
        figuratransporte = []
        tipos_figura = []
        for figura in invoice.figuratransporte_ids:
            tipos_figura = {
                       'TipoFigura': figura.tipofigura.clave,
                       'RFCFigura': figura.figura_id.vat if figura.figura_id.country_id.l10n_mx_edi_code == 'MEX' else '',
                       'NumLicencia': figura.figura_id.cce_licencia,
                       'NombreFigura': figura.figura_id.name,
                       'NumRegIdTribFigura': figura.figura_id.vat if figura.figura_id.country_id.l10n_mx_edi_code != 'MEX' else '',
                       'ResidenciaFiscalFigura': figura.figura_id.country_id.l10n_mx_edi_code if figura.figura_id.country_id.l10n_mx_edi_code != 'MEX' else '',
                       'Domicilio': {
                                'Calle': figura.figura_id.street_name,
                                'NumeroExterior': figura.figura_id.street_number,
                                'NumeroInterior': figura.figura_id.street_number2,
                                'Colonia': figura.figura_id.l10n_mx_edi_colony_code if ubicacion.contacto.country_id.l10n_mx_edi_code == 'MEX' else ubicacion.contacto.l10n_mx_edi_colony or '',
                                'Localidad': figura.figura_id.l10n_mx_edi_locality_id.code if ubicacion.contacto.country_id.l10n_mx_edi_code == 'MEX' else ubicacion.contacto.l10n_mx_edi_locality,
                          #      'Referencia': operador.company_id.cce_clave_estado.c_estado,
                                'Municipio': figura.figura_id.city_id.l10n_mx_edi_code if figura.figura_id.country_id.l10n_mx_edi_code == 'MEX' else figura.figura_id.city,
                                'Estado': figura.figura_id.state_id.code if figura.figura_id.country_id.l10n_mx_edi_code in ('MEX', 'USA', 'CAN') or figura.figura_id.state_id.code else 'NA',
                                'Pais': figura.figura_id.country_id.l10n_mx_edi_code,
                                'CodigoPostal': figura.figura_id.zip,
                       },
            }

            partes = []
            for parte in figura.partetransporte:
               partes.append({
                    'ParteTransporte': parte.clave,
               })
            figuratransporte.append({'TiposFigura': tipos_figura, 'PartesTransporte': partes})

        cartaporte20.update({'FiguraTransporte': figuratransporte})
        vals.update({'cartaporte20': cartaporte20})

      return vals

    def clean_text(self, text):
        clean_text = text.replace('\n', ' ').replace('\\', ' ').replace('-', ' ').replace('/', ' ').replace('|', ' ')
        clean_text = clean_text.replace(',', ' ').replace(';', ' ').replace('>', ' ').replace('<', ' ')
        return clean_text[:1000]
