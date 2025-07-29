from odoo import api, fields, models, _
from odoo.exceptions import UserError


class purchase_order(models.Model):
    _inherit = "purchase.order"

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.auto_generated and self.auto_sale_order_id and \
            self.auto_sale_order_id.invoice_ids:
            inv_id = self.auto_sale_order_id.invoice_ids[0]
            if not inv_id.intercom_expense_acc:
                invoice_vals.update({'to_agency': True})
            if inv_id.sir_id:
                invoice_vals.update({
                    'sir_id': inv_id.sir_id.id,
                    'operation_type': inv_id.operation_type,
                    'pedimento_invoice': inv_id.pedimento_invoice,
                    'number_mark': inv_id.number_mark,
                    'ware': inv_id.ware,
                    'total_package': inv_id.total_package,
                    'reception': inv_id.reception,
                    'order_number': inv_id.order_number,
                    'custom_house': inv_id.custom_house,
                    'ship': inv_id.ship,
                    'supplier': inv_id.supplier,
                    'total_weight': inv_id.total_weight,})
            if inv_id.house_id:
                invoice_vals.update({'sir_id': inv_id.house_id.id})
        return invoice_vals

