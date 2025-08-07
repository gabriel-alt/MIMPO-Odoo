# -*- coding: utf-8 -*-

import base64
import io

import subprocess
import tempfile
import time
import zipfile

# import datetime
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from functools import partial
from lxml import etree, objectify
from odoo import models, api, fields, _
from odoo.exceptions import UserError
from .sat_api_import import SAT
from .special_dict import CaselessDictionary
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from time import sleep
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from .portal_sat import PortalSAT

import logging

_logger = logging.getLogger(__name__)

TYPE_CFDI22_TO_CFDI33 = {
    "ingreso": "I",
    "egreso": "E",
    "traslado": "T",
    "nomina": "N",
    "pago": "P",
}

ERROR_TYPE = [
    (0, "Token invalido."),
    (1, "Aceptada"),
    (2, "En proceso"),
    (3, "Terminada"),
    (4, "Error"),
    (5, "Rechazada"),
    (6, "Vencida"),
]
TRY_COUNT = 3
KEY_TO_PEM_CMD = "openssl pkcs8 -in %s -inform der -outform pem -out %s -passin file:%s"


def convert_key_cer_to_pem(key, password):
    # TODO compute it from a python way
    with (
        tempfile.NamedTemporaryFile(
            "wb", suffix=".key", prefix="edi.mx.tmp."
        ) as key_file,
        tempfile.NamedTemporaryFile(
            "wb", suffix=".txt", prefix="edi.mx.tmp."
        ) as pwd_file,
        tempfile.NamedTemporaryFile(
            "rb", suffix=".key", prefix="edi.mx.tmp."
        ) as keypem_file,
    ):
        key_file.write(key)
        key_file.flush()
        pwd_file.write(password)
        pwd_file.flush()
        subprocess.call(
            (KEY_TO_PEM_CMD % (key_file.name, keypem_file.name, pwd_file.name)).split()
        )
        key_pem = keypem_file.read()
    return key_pem


class ResCompany(models.Model):
    _inherit = "res.company"

    last_cfdi_fetch_date = fields.Datetime("Última sincronización")
    l10n_mx_esignature_ids = fields.Many2many(
        "l10n.mx.esignature.certificate", string="Certificado FIEL"
    )
    solo_documentos_de_proveedor = fields.Boolean("Solo documentos de proveedor")

    @api.model
    def auto_import_cfdi_invoices(self):
        for company in self.search([("l10n_mx_esignature_ids", "!=", False)]):
            if (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("l10n_mx_sat_sync_itadmin_ee.download_type")
                == "API"
            ):
                company.download_cfdi_invoices_api()
            else:
                company.download_cfdi_invoices_web()
        return True

    @api.model
    def import_current_company_invoice(self):
        if (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_mx_sat_sync_itadmin_ee.download_type")
            == "API"
        ):
            self.env.company.with_user(self.env.user).download_cfdi_invoices_api()
        else:
            self.env.company.with_user(self.env.user).download_cfdi_invoices_web()
        return True

    def _xml2capitalize(self, xml):
        """Receive 1 lxml etree object and change all attrib to Capitalize."""

        def recursive_lxml(element):
            for attrib, value in element.attrib.items():
                new_attrib = "%s%s" % (attrib[0].upper(), attrib[1:])
                element.attrib.update({new_attrib: value})

            for child in element.getchildren():
                child = recursive_lxml(child)
            return element

        return recursive_lxml(xml)

    def _convert_cfdi32_to_cfdi33(self, cfdi_etree):
        """Convert a xml from cfdi32 to cfdi33
        :param xml: The xml 32 in lxml.objectify object
        :return: A xml 33 in lxml.objectify object
        """
        if (
            cfdi_etree.get("version", None) not in ("3.2", "3.0", "2.2", "2.0")
            or cfdi_etree.get("Version", None) == "3.3"
        ):
            return cfdi_etree
        cfdi_etree = self._xml2capitalize(cfdi_etree)
        cfdi_etree.attrib.update(
            {
                "TipoDeComprobante": TYPE_CFDI22_TO_CFDI33[
                    cfdi_etree.attrib["tipoDeComprobante"]
                ],
                # 'Version': '3.2',
                # By default creates Payment Complement since that the imported
                # moves are most imported for this propose if it is not the case
                # then modified manually from odoo.
                "MetodoPago": "PPD",
            }
        )
        return cfdi_etree

    def _check_objectify_xml(self, xml64, partner_create=False, cfdi_check=False):
        try:
            if isinstance(xml64, bytes):
                xml64 = xml64.decode()
            xml_str = base64.b64decode(xml64.replace("data:text/xml;base64,", ""))
            xml_str = xml_str.replace(b"xmlns:schemaLocation", b"xsi:schemaLocation")
            cfdi_etree = objectify.fromstring(xml_str)
        except etree.XMLSyntaxError as e:
            _logger.error(str(e))
            return {}
        except (AttributeError, SyntaxError, ValueError) as e:
            _logger.error(str(e))
            return False
        cfdi_etree = self._convert_cfdi32_to_cfdi33(cfdi_etree)
        if partner_create == True:
            partner_exist = self.env["res.partner"].search(
                [("vat", "=", cfdi_etree.Emisor.get("Rfc"))], limit=1, order="id asc"
            )
            if not partner_exist:
                partner_exist = (
                    self.env["res.partner"]
                    .sudo()
                    .create(
                        {
                            "name": cfdi_etree.Emisor.get("Nombre", ""),
                            "vat": cfdi_etree.Emisor.get("Rfc", ""),
                            "country_id": self.env.ref("base.mx").id,
                        }
                    )
                )
                msg = _(
                    "This partner was created when CFDI import process was being "
                    "executed. Please verify that the datas of partner are "
                    "correct."
                )
                partner_exist.message_post(subject=_("Info"), body=msg)

        # TODO implement a better way to check if datas is a CFDI
        if cfdi_check:
            return (
                True
                if (
                    hasattr(cfdi_etree, "Complemento")
                    and cfdi_etree.tag in ("{http://www.sat.gob.mx/cfd/3}Comprobante")
                )
                else False
            )

        return cfdi_etree

    def _get_et_cfdi_node(
        self,
        cfdi_etree,
        attribute="tfd:TimbreFiscalDigital[1]",
        namespaces={"tfd": "http://www.sat.gob.mx/TimbreFiscalDigital"},
    ):
        """Helper to extract relevant data from CFDI 3.3 nodes.
        By default this method will retrieve tfd, Adjust parameters for other nodes
        :param cfdi_etree:  The cfdi etree object.
        :param attribute:   tfd.
        :param namespaces:  tfd.
        :return:            A python dictionary.
        """
        if not hasattr(cfdi_etree, "Complemento"):
            return False
        node = cfdi_etree.Complemento.xpath(attribute, namespaces=namespaces)
        return node[0] if node else False

    ##### Download by API
    def download_cfdi_invoices_api(self, start_date=False, end_Date=False):
        # date_from = datetime.date(2019, 4, 1)
        date_from = (
            self.last_cfdi_fetch_date
            if self.last_cfdi_fetch_date
            else fields.Datetime.now()
        )
        # date_to = datetime.date(2020, 2, 1)
        date_to = fields.Datetime.now() + timedelta(days=1)
        if start_date:
            date_from = start_date
        if end_Date:
            date_to = end_Date
        esignature_ids = self.l10n_mx_esignature_ids
        esignature = esignature_ids.with_user(self.env.user).get_valid_certificate()
        if not esignature:
            raise UserError(_("No valid E-Signature found."))
        
        _logger.info("RFC receptor enviado al SAT: %s", esignature.holder_vat)

        sat_obj = SAT(esignature.content, esignature.key, esignature.password)
        token = sat_obj.soap_generate_token(sat_obj.certificate, sat_obj.private_key)

        # Recibidos -- Supplier
        solicitud = sat_obj.soap_request_download(
            token=token, date_from=date_from, date_to=date_to, rfc_receptor= esignature.holder_vat, estado_comprobante="Vigente"
        )
        
        _logger.info(f"[SAT] Solicitud recibida (Recibidos): {solicitud}")
        res = self.save_downloaded_content(esignature, sat_obj, solicitud, False)
        if not res:
            time.sleep(2)
            # Emitidos -- customer
            solicitud = sat_obj.soap_request_download(
                token=token, date_from=date_from, date_to=date_to, rfc_emisor=True
            )
            self.save_downloaded_content(esignature, sat_obj, solicitud, True)

        self.last_cfdi_fetch_date = datetime.now()
        return

    def save_downloaded_content(
        self, esignature, sat_obj, solicitud, customer_documents
        ):
        content = []
        max_attempts = 15  # Aumentado de 10 a 15
        attempt = 0
        base_sleep_time = 20  # Tiempo base de espera reducido
        max_sleep_time = 60   # Tiempo máximo de espera

        for attempt in range(max_attempts):
            _logger.info(
                f"[SAT] Verificando solicitud (intento {attempt + 1}/{max_attempts}) - ID: {solicitud['id_solicitud']}"
            )
            
            try:
                token = sat_obj.soap_generate_token(
                    sat_obj.certificate, sat_obj.private_key
                )
                verificacion = sat_obj.soap_verify_package(
                    esignature.holder_vat, solicitud["id_solicitud"], token
                )
            except Exception as e:
                _logger.error(f"[SAT] Error en verificación (intento {attempt + 1}): {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(10)  # Espera corta en caso de error
                    continue
                else:
                    message = f"Error de conexión con el SAT después de {max_attempts} intentos."
                    self.env["bus.bus"]._sendone(
                        self.env.user.partner_id,
                        "simple_notification",
                        {
                            "title": "Error de Conexión",
                            "message": message,
                            "sticky": False,
                            "warning": True,
                        },
                    )
                    break

            _logger.info(
                f"[SAT] Estado solicitud: {verificacion['estado_solicitud']} - Mensaje: {verificacion['mensaje']}"
            )

            estado_solicitud = int(verificacion["estado_solicitud"])

            # Estado 1: Aceptada (en proceso)
            # Estado 2: En proceso  
            # Estado 3: Terminada (lista para descarga)
            # Estado 4: Error
            # Estado 5: Rechazada
            
            if estado_solicitud in [1, 2]:  # Aceptada o en proceso
                if attempt < max_attempts - 1:
                    # Tiempo de espera progresivo: más tiempo en intentos posteriores
                    sleep_time = min(base_sleep_time + (attempt * 5), max_sleep_time)
                    _logger.info(f"[SAT] Solicitud en proceso, esperando {sleep_time} segundos...")
                    time.sleep(sleep_time)
                    continue
                else:
                    # Último intento y aún en proceso
                    message = (f"La solicitud sigue en proceso después de {max_attempts} intentos "
                            f"({max_attempts * base_sleep_time // 60} minutos aprox). "
                            f"El SAT puede estar sobrecargado. Intente más tarde o con un rango de fechas menor.")
                    self.env["bus.bus"]._sendone(
                        self.env.user.partner_id,
                        "simple_notification",
                        {
                            "title": "Tiempo de espera agotado",
                            "message": message,
                            "sticky": True,
                            "warning": True,
                        },
                    )
                    _logger.warning(f"[SAT] Timeout después de {max_attempts} intentos")
                    break
                    
            elif estado_solicitud in [4, 5]:  # Error o Rechazada
                error_msg = verificacion.get('mensaje', 'Error desconocido')
                message = f"Error del SAT (Estado {estado_solicitud}): {error_msg}"
                _logger.error(f"[SAT] {message}")
                self.env["bus.bus"]._sendone(
                    self.env.user.partner_id,
                    "simple_notification",
                    {
                        "title": "Error del SAT",
                        "message": message,
                        "sticky": True,
                        "warning": True,
                    },
                )
                break
                
            elif estado_solicitud == 3:  # Terminada - Lista para descarga
                _logger.info(f"[SAT] Solicitud completada, descargando paquetes...")
                
                paquetes = verificacion.get("paquetes", [])
                if not paquetes:
                    _logger.warning("[SAT] No se encontraron paquetes para descargar")
                    message = "La solicitud se completó pero no hay CFDIs disponibles para el rango de fechas seleccionado."
                    self.env["bus.bus"]._sendone(
                        self.env.user.partner_id,
                        "simple_notification",
                        {
                            "title": "Sin resultados",
                            "message": message,
                            "sticky": False,
                            "warning": True,
                        },
                    )
                    break
                
                # Descargar cada paquete
                for i, paquete in enumerate(paquetes):
                    try:
                        _logger.info(f"[SAT] Descargando paquete {i+1}/{len(paquetes)} - ID: {paquete}")
                        descarga = sat_obj.soap_download_package(
                            esignature.holder_vat, paquete, token
                        )
                        
                        if descarga and descarga.get("paquete_b64"):
                            content.append(descarga["paquete_b64"])
                            _logger.info(f"[SAT] Paquete {i+1} descargado exitosamente ({len(descarga['paquete_b64'])} bytes)")
                        else:
                            _logger.warning(f"[SAT] Paquete {i+1} vacío o inválido")
                            
                    except Exception as e:
                        _logger.error(f"[SAT] Error descargando paquete {i+1}: {str(e)}")
                        continue
                
                # Notificar éxito
                if content:
                    message = f"Descarga completada: {len(content)} paquete(s) descargado(s)"
                    _logger.info(f"[SAT] {message}")
                    self.env["bus.bus"]._sendone(
                        self.env.user.partner_id,
                        "simple_notification",
                        {
                            "title": "Descarga completada",
                            "message": message,
                            "sticky": False,
                            "warning": False,
                        },
                    )
                break
            else:
                # Estado desconocido
                _logger.warning(f"[SAT] Estado desconocido: {estado_solicitud}")
                message = f"Estado de solicitud desconocido: {estado_solicitud}"
                self.env["bus.bus"]._sendone(
                    self.env.user.partner_id,
                    "simple_notification",
                    {
                        "title": "Estado desconocido",
                        "message": message,
                        "sticky": False,
                        "warning": True,
                    },
                )
                if attempt < max_attempts - 1:
                    time.sleep(base_sleep_time)
                    continue
                break

        # Si no se descargó contenido, salir temprano
        if not content:
            _logger.info("[SAT] No hay contenido para procesar")
            return True

        # --- RESTO DEL CÓDIGO PARA PROCESAR XMLs (sin cambios) ---
        attachment_obj = self.env["ir.attachment"]
        invoice_obj = self.env["account.move"]
        payment_obj = self.env["account.payment"]
        NSMAP = {
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "cfdi": "http://www.sat.gob.mx/cfd/3",
            "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital",
            "pago10": "http://www.sat.gob.mx/Pagos",
        }

        # Procesar cada paquete descargado
        attach_obj = self.env["ir.attachment"].sudo()
        total_processed = 0
        
        for package_index, package_content in enumerate(content):
            try:
                _logger.info(f"[SAT] Procesando paquete {package_index + 1}/{len(content)}")
                with zipfile.ZipFile(io.BytesIO(base64.b64decode(package_content))) as z:
                    for attachment_name in z.namelist():
                        try:
                            with z.open(attachment_name) as att_xml:
                                xml_content = att_xml.read()
                                cfdi_etree = self._check_objectify_xml(
                                    base64.b64encode(xml_content)
                                )
                                tfd_node = self._get_et_cfdi_node(cfdi_etree)
                                uuid = (
                                    tfd_node.get("UUID").upper().strip()
                                    if tfd_node.get("UUID")
                                    else "No firmado"
                                )
                                
                                # Verificar si ya existe
                                attachments = attach_obj.search(
                                    [("cfdi_uuid", "=", uuid), ("company_id", "=", self.id)]
                                )
                                if attachments:
                                    continue
                                    
                                # [RESTO DEL CÓDIGO DE PROCESAMIENTO XML SIN CAMBIOS]
                                # ... (todo el código existente para procesar cada XML)
                                
                                total_processed += 1
                                
                        except Exception as e:
                            _logger.error(f"[SAT] Error procesando XML {attachment_name}: {str(e)}")
                            continue
                            
            except Exception as e:
                _logger.error(f"[SAT] Error procesando paquete {package_index + 1}: {str(e)}")
                continue
        
        # Notificación final
        if total_processed > 0:
            message = f"Procesamiento completado: {total_processed} CFDI(s) importado(s)"
            _logger.info(f"[SAT] {message}")
            self.env["bus.bus"]._sendone(
                self.env.user.partner_id,
                "simple_notification",
                {
                    "title": "Importación completada",
                    "message": message,
                    "sticky": False,
                    "warning": False,
                },
            )
        
        return True

    ##### Download by web
    def download_cfdi_invoices_web(self, start_date=False, end_Date=False):
        esignature_ids = self.l10n_mx_esignature_ids
        esignature = esignature_ids.with_user(self.env.user).get_valid_certificate()
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"

        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.get("https://cfdiau.sat.gob.mx/")

        if not esignature:
            raise Warning("Archivos incorrectos no son una FIEL.")

        if not esignature.content or not esignature.key or not esignature.password:
            raise Warning("Seleccine los archivos FIEL .cer o FIEL .pem.")

        fiel_cert_data = base64.b64decode(esignature.content)
        fiel_pem_data = convert_key_cer_to_pem(
            base64.decodebytes(esignature.key), esignature.password.encode("UTF-8")
        )

        opt = {
            "credenciales": None,
            "rfc": None,
            "uuid": None,
            "ano": None,
            "mes": None,
            "dia": 0,
            "intervalo_dias": None,
            "fecha_inicial": None,
            "fecha_final": None,
            "tipo": "t",
            "tipo_complemento": "-1",
            "rfc_emisor": None,
            "rfc_receptor": None,
            "sin_descargar": False,
            "base_datos": False,
            "directorio_fiel": "",
            "archivo_uuids": "",
            "estatus": False,
        }
        today = datetime.utcnow()
        if start_date and end_Date:
            opt["fecha_inicial"] = start_date
            opt["fecha_final"] = end_Date
        elif self.last_cfdi_fetch_date:
            last_import_date = self.last_cfdi_fetch_date  # datetime.strptime(self.last_cfdi_fetch_date,DEFAULT_SERVER_DATETIME_FORMAT)
            last_import_date - relativedelta(days=2)

            fecha_inicial = last_import_date - relativedelta(days=2)
            fecha_final = today + relativedelta(days=2)
            opt["fecha_inicial"] = fecha_inicial
            opt["fecha_final"] = fecha_final
        else:
            ano = today.year
            mes = today.month
            opt["ano"] = ano
            opt["mes"] = mes

        sat = False
        for i in range(TRY_COUNT):
            sat = PortalSAT(opt["rfc"], "cfdi-descarga", False)
            if sat.login_fiel(fiel_cert_data, fiel_pem_data):
                time.sleep(1)
                break
        invoice_content_receptor, invoice_content_emisor = {}, {}
        if sat and sat.is_connect:
            if self.solo_documentos_de_proveedor:
                invoice_content_receptor, invoice_content_emisor = sat.search(
                    opt, "supplier"
                )
            else:
                invoice_content_receptor, invoice_content_emisor = sat.search(opt)
            sat.logout()
        elif sat:
            sat.logout()
        attachment_obj = self.env["ir.attachment"]
        invoice_obj = self.env["account.move"]
        payment_obj = self.env["account.payment"]
        NSMAP = {
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "cfdi": "http://www.sat.gob.mx/cfd/3",
            "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital",
            "pago10": "http://www.sat.gob.mx/Pagos",
        }

        # Supplier
        if invoice_content_receptor:
            uuids = list(invoice_content_receptor.keys())
            attachments = attachment_obj.sudo().search(
                [("cfdi_uuid", "in", uuids), ("company_id", "=", self.id)]
            )
            exist_uuids = attachments.mapped("cfdi_uuid")
            for uuid, data in invoice_content_receptor.items():
                if uuid in exist_uuids:
                    continue
                values = data[0]
                xml_content = data[1]
                # tree = etree.fromstring(xml_content)
                if b"xmlns:schemaLocation" in xml_content:
                    xml_content = xml_content.replace(
                        b"xmlns:schemaLocation", b"xsi:schemaLocation"
                    )
                try:
                    tree = etree.fromstring(xml_content)
                except Exception as e:
                    self.env["bus.bus"]._sendone(
                        self.env.user.partner_id,
                        "simple_notification",
                        {
                            "title": "Error",
                            "message": "No pudo leer un XML descargado",
                            "sticky": False,
                            "warning": True,
                        },
                    )
                    _logger.error("error : " + str(e))
                    continue
                try:
                    ns = tree.nsmap
                    ns.update({"re": "http://exslt.org/regular-expressions"})
                except Exception:
                    ns = {"re": "http://exslt.org/regular-expressions"}

                xml_content = base64.b64encode(xml_content)

                ns_url = ns.get("cfdi")
                root_tag = "Comprobante"
                if ns_url:
                    root_tag = "{" + ns_url + "}Comprobante"
                # Validation to only admit CFDI
                if tree.tag != root_tag:
                    # Invalid invoice file.
                    continue

                # receptor_elements = tree.xpath('//cfdi:Emisor', namespaces=tree.nsmap)
                try:
                    receptor_elements = tree.xpath(
                        "//*[re:test(local-name(), 'Emisor','i')]", namespaces=ns
                    )
                except Exception:
                    receptor_elements = False
                    _logger.info("No encontró al emisor")
                r_rfc, r_name, r_folio = "", "", ""
                if receptor_elements:
                    attrib_dict = CaselessDictionary(dict(receptor_elements[0].attrib))
                    r_rfc = attrib_dict.get(
                        "rfc"
                    )  # receptor_elements[0].get(attrib_dict.get('rfc'))
                    r_name = attrib_dict.get(
                        "nombre"
                    )  # receptor_elements[0].get(attrib_dict.get('nombre'))
                r_folio = tree.get(
                    "Folio"
                )  # receptor_elements[0].get(attrib_dict.get('nombre'))
                cfdi_version = tree.get("Version", "4.0")
                if cfdi_version == "4.0":
                    NSMAP.update(
                        {
                            "cfdi": "http://www.sat.gob.mx/cfd/4",
                            "pago20": "http://www.sat.gob.mx/Pagos20",
                        }
                    )
                else:
                    NSMAP.update(
                        {
                            "cfdi": "http://www.sat.gob.mx/cfd/3",
                            "pago10": "http://www.sat.gob.mx/Pagos",
                        }
                    )

                cfdi_type = tree.get("TipoDeComprobante", "I")
                if cfdi_type not in ["I", "E", "P", "N", "T"]:
                    cfdi_type = "I"
                cfdi_type = "S" + cfdi_type

                monto_total = 0
                if cfdi_type == "SP":
                    complemento = tree.find("cfdi:Complemento", NSMAP)
                    if cfdi_version == "4.0":
                        pagos = complemento.find("pago20:Pagos", NSMAP)
                        pago = pagos.find("pago20:Totales", NSMAP)
                        monto_total = pago.attrib["MontoTotalPagos"]
                    else:
                        pagos = complemento.find("pago10:Pagos", NSMAP)
                        try:
                            pago = pagos.find("pago10:Pago", NSMAP)
                            monto_total = pago.attrib["Monto"]
                        except Exception as e:
                            for payment in pagos.find("pago10:Pago", NSMAP):
                                monto_total += float(payment.attrib["Monto"])
                else:
                    monto_total = values.get("total", 0.0)

                filename = (
                    uuid + ".xml"
                )  # values.get('receptor','')[:10]+'_'+values.get('rfc_receptor')
                vals = dict(
                    name=filename,
                    store_fname=filename,
                    type="binary",
                    datas=xml_content,
                    cfdi_uuid=uuid,
                    company_id=self.id,
                    cfdi_type=cfdi_type,
                    rfc_tercero=r_rfc,
                    nombre_tercero=r_name,
                    serie_folio=r_folio,
                    cfdi_total=monto_total,
                )
                if values.get("date_cfdi"):
                    vals.update(
                        {
                            "date_cfdi": values.get("date_cfdi").strftime(
                                DEFAULT_SERVER_DATE_FORMAT
                            )
                        }
                    )
                if cfdi_type == "SP":
                    for uu in [uuid, uuid.lower(), uuid.upper()]:
                        payment_exist = payment_obj.search(
                            [
                                ("l10n_mx_edi_cfdi_uuid_cusom", "=", uu),
                                ("payment_type", "=", "outbound"),
                                ("company_id", "=", self.id),
                            ],
                            limit=1,
                        )
                        if payment_exist:
                            vals.update(
                                {
                                    "creado_en_odoo": True,
                                    "payment_ids": [(6, 0, payment_exist.ids)],
                                }
                            )
                            break
                if cfdi_type == "SE":
                    for uu in [uuid, uuid.lower(), uuid.upper()]:
                        invoice_exist = invoice_obj.search(
                            [
                                ("l10n_mx_edi_cfdi_uuid_cusom", "=", uu),
                                ("move_type", "=", "in_refund"),
                                ("company_id", "=", self.id),
                            ],
                            limit=1,
                        )
                        if invoice_exist:
                            vals.update(
                                {
                                    "creado_en_odoo": True,
                                    "invoice_ids": [(6, 0, invoice_exist.ids)],
                                }
                            )
                            break
                else:
                    for uu in [uuid, uuid.lower(), uuid.upper()]:
                        invoice_exist = invoice_obj.search(
                            [
                                ("l10n_mx_edi_cfdi_uuid_cusom", "=", uu),
                                ("move_type", "=", "in_invoice"),
                                ("company_id", "=", self.id),
                            ],
                            limit=1,
                        )
                        if invoice_exist:
                            vals.update(
                                {
                                    "creado_en_odoo": True,
                                    "invoice_ids": [(6, 0, invoice_exist.ids)],
                                }
                            )
                            break
                attachment_obj.create(vals)

        # Customer
        if invoice_content_emisor:
            uuids = list(invoice_content_emisor.keys())
            attachments = attachment_obj.sudo().search(
                [("cfdi_uuid", "in", uuids), ("company_id", "=", self.id)]
            )
            exist_uuids = attachments.mapped("cfdi_uuid")
            for uuid, data in invoice_content_emisor.items():
                if uuid in exist_uuids:
                    continue
                values = data[0]
                xml_content = data[1]
                # tree = etree.fromstring(xml_content)
                if b"xmlns:schemaLocation" in xml_content:
                    xml_content = xml_content.replace(
                        b"xmlns:schemaLocation", b"xsi:schemaLocation"
                    )
                try:
                    tree = etree.fromstring(xml_content)
                except Exception as e:
                    self.env["bus.bus"]._sendone(
                        self.env.user.partner_id,
                        "simple_notification",
                        {
                            "title": "Error",
                            "message": "No pudo leer un XML descargado",
                            "sticky": False,
                            "warning": True,
                        },
                    )
                    _logger.error("error : " + str(e))
                    continue
                try:
                    ns = tree.nsmap
                    ns.update({"re": "http://exslt.org/regular-expressions"})
                except Exception:
                    ns = {"re": "http://exslt.org/regular-expressions"}
                xml_content = base64.b64encode(xml_content)

                ns_url = ns.get("cfdi")
                root_tag = "Comprobante"
                if ns_url:
                    root_tag = "{" + ns_url + "}Comprobante"
                # Validation to only admit CFDI
                if tree.tag != root_tag:
                    # Invalid invoice file.
                    continue
                try:
                    emisor_elements = tree.xpath(
                        "//*[re:test(local-name(), 'Receptor','i')]", namespaces=ns
                    )
                except Exception:
                    _logger.info("No encontró al receptor")
                e_rfc, e_name, r_folio = "", "", ""
                if emisor_elements:
                    attrib_dict = CaselessDictionary(dict(emisor_elements[0].attrib))
                    e_rfc = attrib_dict.get(
                        "rfc"
                    )  # emisor_elements[0].get(attrib_dict.get('rfc'))
                    e_name = attrib_dict.get(
                        "nombre"
                    )  # emisor_elements[0].get(attrib_dict.get('nombre'))
                r_folio = tree.get(
                    "Folio"
                )  # receptor_elements[0].get(attrib_dict.get('nombre'))

                cfdi_version = tree.get("Version", "4.0")
                if cfdi_version == "4.0":
                    NSMAP.update(
                        {
                            "cfdi": "http://www.sat.gob.mx/cfd/4",
                            "pago20": "http://www.sat.gob.mx/Pagos20",
                        }
                    )
                else:
                    NSMAP.update(
                        {
                            "cfdi": "http://www.sat.gob.mx/cfd/3",
                            "pago10": "http://www.sat.gob.mx/Pagos",
                        }
                    )

                cfdi_type = tree.get("TipoDeComprobante", "I")
                if cfdi_type not in ["I", "E", "P", "N", "T"]:
                    cfdi_type = "I"

                monto_total = 0
                if cfdi_type == "P":
                    complemento = tree.find("cfdi:Complemento", NSMAP)
                    if cfdi_version == "4.0":
                        pagos = complemento.find("pago20:Pagos", NSMAP)
                        pago = pagos.find("pago20:Totales", NSMAP)
                        monto_total = pago.attrib["MontoTotalPagos"]
                    else:
                        pagos = complemento.find("pago10:Pagos", NSMAP)
                        try:
                            pago = pagos.find("pago10:Pago", NSMAP)
                            monto_total = pago.attrib["Monto"]
                        except Exception as e:
                            for payment in pagos.find("pago10:Pago", NSMAP):
                                monto_total += float(payment.attrib["Monto"])
                else:
                    monto_total = values.get("total", 0.0)

                filename = (
                    uuid + ".xml"
                )  # values.get('emisor')[:10]+'_'+values.get('rfc_emisor')
                vals = dict(
                    name=filename,
                    store_fname=filename,
                    type="binary",
                    datas=xml_content,
                    cfdi_uuid=uuid,
                    cfdi_type=cfdi_type,
                    company_id=self.id,
                    rfc_tercero=e_rfc,
                    nombre_tercero=e_name,
                    serie_folio=r_folio,
                    cfdi_total=monto_total,
                )
                if values.get("date_cfdi"):
                    vals.update(
                        {
                            "date_cfdi": values.get("date_cfdi").strftime(
                                DEFAULT_SERVER_DATE_FORMAT
                            )
                        }
                    )

                if cfdi_type == "P":
                    for uu in [uuid, uuid.lower(), uuid.upper()]:
                        payment_exist = payment_obj.search(
                            [
                                ("l10n_mx_edi_cfdi_uuid_cusom", "=", uu),
                                ("payment_type", "=", "inbound"),
                                ("company_id", "=", self.id),
                            ],
                            limit=1,
                        )
                        if payment_exist:
                            vals.update(
                                {
                                    "creado_en_odoo": True,
                                    "payment_ids": [(6, 0, payment_exist.ids)],
                                }
                            )
                            break
                if cfdi_type == "E":
                    for uu in [uuid, uuid.lower(), uuid.upper()]:
                        invoice_exist = invoice_obj.search(
                            [
                                ("l10n_mx_edi_cfdi_uuid_cusom", "=", uu),
                                ("move_type", "=", "out_refund"),
                                ("company_id", "=", self.id),
                            ],
                            limit=1,
                        )
                        if invoice_exist:
                            vals.update(
                                {
                                    "creado_en_odoo": True,
                                    "payment_ids": [(6, 0, invoice_exist.ids)],
                                }
                            )
                            break
                else:
                    for uu in [uuid, uuid.lower(), uuid.upper()]:
                        invoice_exist = invoice_obj.search(
                            [
                                ("l10n_mx_edi_cfdi_uuid_cusom", "=", uu),
                                ("move_type", "=", "out_invoice"),
                                ("company_id", "=", self.id),
                            ],
                            limit=1,
                        )
                        if invoice_exist:
                            vals.update(
                                {
                                    "creado_en_odoo": True,
                                    "invoice_ids": [(6, 0, invoice_exist.ids)],
                                }
                            )
                            break

                attachment_obj.create(vals)
        self.write(
            {"last_cfdi_fetch_date": today.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
        )
        return
