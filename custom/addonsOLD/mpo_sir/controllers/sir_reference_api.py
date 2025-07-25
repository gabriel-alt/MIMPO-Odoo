from schema import Schema, Optional, Or, Use

from odoo.http import request
from odoo import http

class ReferenceAPI(http.Controller):

    @http.route([
        '/v1/api/reference'
    ], type='json', auth='api_key', methods=['POST'], csrf=False, log_req=True)
    # @api_route(auth=True,log_req=True)
    def create_product(self, **params):
        return self._create_product(**params)

    def _create_product(self, **params):
        rules = Schema({
            'ref_id': int,
            'number': str,
            'pedimento': str,
            'patent_code': str,
            'customer': str,
            'partner_id': int,
            'operation_type': int,
            'ref_document': str,
            Optional('total_weight'): float,
            Optional('total_custom_house'): float,
            Optional('invoice_value'): float,
            Optional('total_sale'): float,
            Optional('type_rate'): float,
            Optional('container_qty'): int,
            Optional('sliced_group'): int,
            Optional('non_sliced_group'): int,
            Optional('non_paid_tax'): float,
            Optional('paid_tax'): float,
            Optional('guide_qty'): int,
            Optional('total_package'): int,
            Optional('total_padlock'): int,
            Optional('total_remittance'): int,
            Optional('total_invoice'): int,
            Optional('total_cove'): int,
            Optional('total_part'): int,
            Optional('total_eDocument'): int,
            Optional('amount_dta'): float,
            Optional('amount_adv'): float,
            Optional('amount_ieps'): float,
            Optional('amount_other'): float,
            Optional('amount_iva'): float,
            Optional('amount_insurance'): float,
            Optional('amount_expense'): float,
            Optional('amount_ded_other'): float,
            Optional('total_inc'): float,
            Optional('amount_ph'): float,
            Optional('date_ph'): str,
            Optional('pece_account'): bool,
            Optional('pedimento_date'): str,
            Optional('custom_house'): str,
            Optional('pedimento_invoice'): str,
            Optional('number_mark'): str,
            Optional('ware'): str,
            Optional('reception'): str,
            Optional('order_number'): str,
            Optional('ship'): str,
            Optional('supplier'): str,
        }, ignore_extra_keys=True,)
        model = request.env['sir.ref']
        overwrites = {}

        return model.post_record(params, rules, overwrites)
    
    @http.route(
        '/v1/api/reference/<int:ref_id>',
        type='json', auth='public', methods=['PUT', 'PATCH'], csrf=False, log_req=True)
    # @api_route(auth=True,log_req=True)
    def putReference(self, ref_id, **params):
        # params['partner_id'] = request.env.ref('base.main_company').partner_id.id
        # params['company_id'] = request.env.ref('base.main_company').id
        # define data-types rules
        rules = Schema({
            Optional('ref_id'): int,
            Optional('number'): str,
            Optional('pedimento'): str,
            Optional('patent_code'): str,
            Optional('customer'): str,
            Optional('partner_id'): int,
            Optional('operation_type'): int,
            Optional('ref_document'): str,
            Optional('total_weight'): float,
            Optional('total_custom_house'): float,
            Optional('invoice_value'): float,
            Optional('total_sale'): float,
            Optional('type_rate'): float,
            Optional('container_qty'): int,
            Optional('sliced_group'): int,
            Optional('non_sliced_group'): int,
            Optional('non_paid_tax'): float,
            Optional('paid_tax'): float,
            Optional('guide_qty'): int,
            Optional('total_package'): int,
            Optional('total_padlock'): int,
            Optional('total_remittance'): int,
            Optional('total_invoice'): int,
            Optional('total_cove'): int,
            Optional('total_part'): int,
            Optional('total_eDocument'): int,
            Optional('amount_dta'): float,
            Optional('amount_adv'): float,
            Optional('amount_ieps'): float,
            Optional('amount_other'): float,
            Optional('amount_iva'): float,
            Optional('amount_insurance'): float,
            Optional('amount_expense'): float,
            Optional('amount_ded_other'): float,
            Optional('total_inc'): float,
            Optional('amount_ph'): float,
            Optional('date_ph'): str,
            Optional('pece_account'): bool,
            Optional('pedimento_date'): str,
            Optional('custom_house'): str,
            Optional('pedimento_invoice'): str,
            Optional('number_mark'): str,
            Optional('ware'): str,
            Optional('reception'): str,
            Optional('order_number'): str,
            Optional('ship'): str,
            Optional('supplier'): str,
        }, ignore_extra_keys=True,)
        model = request.env['sir.ref'].sudo()

        # add this params to run convert country code to Odoo country ID
        overwrites = {}

        return model.browse(ref_id).put_record(params, rules, overwrites)