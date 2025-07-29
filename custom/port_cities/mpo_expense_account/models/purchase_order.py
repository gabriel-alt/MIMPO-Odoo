'''purchase.order'''
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    '''inherit purchase.order'''

    _inherit = 'purchase.order'

    READONLY_STATE = {
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    to_agency = fields.Boolean('A Agencia', tracking=True, states=READONLY_STATE)

    @api.onchange('to_agency')
    def _onchange_to_agency(self):
        '''validation of to_agency changes'''

        if self.state == 'purchase' and self.invoice_ids:
            if self.invoice_ids.filtered(lambda i: i.state=='posted'):
                raise UserError(_("Can't change A Agencia because PO Already Confirmed and "
                    "Bill(s) Already Posted!"))
            else:
                msg = _('The attribute "To agency" will be modified in the Related Vendor Bills')
                warning = {
                    'title': _('Warning for %s', self.name),
                    'message': msg
                }
                return {'warning': warning}

    def update_bills_account(self):
        """ Update Account in the Related Bills """

        for order in self:
            if order.state=='purchase' and order.invoice_ids:
                for inv in self.invoice_ids:
                    if not self.to_agency:
                        for line in inv.invoice_line_ids:
                            line.product_id._check_account_third_party()
                            line.account_id=line.product_id.property_payment_third_party_account_id.id
                    else:
                        for line in inv.invoice_line_ids:
                            line.account_id = line._get_account_product()
                    inv.to_agency=order.to_agency

    def write(self, vals):
        '''extend to update account'''

        res = super(PurchaseOrder, self).write(vals)
        if 'to_agency' in vals:
            self.update_bills_account()
        return res

    def _prepare_invoice(self):
        '''extend to add is_agency to include in data preparation'''

        res = super(PurchaseOrder, self)._prepare_invoice()
        res['to_agency'] = self.to_agency
        return res


class PurchaseOrderLine(models.Model):
    '''inherit purchase.order.line'''

    _inherit = 'purchase.order.line'

    def _prepare_account_move_line(self, move=False):
        '''extend to change account_id based on to_agency rules'''

        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        if not self.order_id.to_agency:
            self.product_id._check_account_third_party()
            res['account_id'] = self.product_id.property_payment_third_party_account_id.id
        return res
