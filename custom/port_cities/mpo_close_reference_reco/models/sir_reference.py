# -*- coding: utf-8 -*-

from odoo import models, fields, api, http
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
import json
import requests
import logging
_logger = logging.getLogger(__name__)

reco_url = 'http://192.168.11.21:81/SIRServicesApi/api/Referencia/CambiaStatus'
api_token = 'M1mp0S3rvic3s'

class CveTransporte(models.Model):
    _inherit = 'sir.ref'

    def write(self, vals):
        res = super(CveTransporte, self).write(vals)
        reco_vals = False
        if vals.get('state', False) == 'open':
            reco_vals = {
                'IdReferencia': self.id,
                'FechaCierre': None
            }
        elif vals.get('state', False) == 'close':
            reco_vals = {
                'IdReferencia': self.id,
                'FechaCierre': fields.Date.to_string(fields.Date.today())
            }
        if reco_vals:
            url = reco_url
            token = api_token
            headers = {
                'APIKey': 'M1mp0S3rvic3s',
                'Content-Type': 'application/json'
            }
            _logger.info('CTX: %s', str(self._context))
            _logger.info('vals: %s', str(vals))
            _logger.info('reco_vals: %s', str(reco_vals))
            body = json.dumps(reco_vals)
            #Add try exception like revuelta weighthing
            #response = requests.put(url, headers=headers, data=body)
            #_logger.info('response: %s', str(response))
            #if response.status_code == 200:
            #    _logger.info('*'*10)
            #    _logger.info('Status 200: %s', str(response.content))
            #    _logger.info('*'*10)

        return res
