'''account.move'''
from odoo import api, fields, models, _


class AccountMove(models.Model):
    '''inherit account.move'''

    _inherit = 'account.move'

    READONLY_STATE = {
        'posted': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    to_agency = fields.Boolean('A Agencia', tracking=True, states=READONLY_STATE)
    rfc_client = fields.Char('RFC', readonly=True)
    client_id = fields.Many2one('res.partner', string='Customer', readonly=True)

    @api.onchange('to_agency')
    def _onchange_to_agency(self):
        '''validation of to_agency changes'''
        if self.state == 'draft' and not self.to_agency:
            self.invoice_line_ids._compute_account_id()
            self.invoice_line_ids.update({'tax_ids': [(6, 0, [])]})
        if self.state == 'draft' and self.invoice_line_ids.filtered(lambda l: l.purchase_order_id):
            purchase = ""
            orders = self.env['purchase.order']
            for order in self.invoice_line_ids.mapped('purchase_order_id'):
                orders |= order
                if not purchase:
                    purchase = order.name
                else:
                    purchase += ', '+order.name
            orders.write({'to_agency': self.to_agency})
            msg = _('The attribute "To agency" will be modified in the purchase order ')
            msg += purchase
            warning = {
                'title': _('Warning for %s', self.name),
                'message': msg
            }
            return {'warning': warning}

    # def update_agency_line_account(self):
    #     """ Update Line account Depending on To Agency """

    #     for move in self:
    #         if move.state=='draft' and move.move_type in ('in_invoice', 'in_refund'):
    #             for line in move.invoice_line_ids:
    #                 if not move.to_agency:
    #                     line.product_id._check_account_third_party()
    #                     line.account_id=line.product_id.property_payment_third_party_account_id.id
    #                 else:
    #                     line.account_id=line._get_account_product()

    # def write(self, vals):
    #     '''extend to update account'''

    #     res = super(AccountMove, self).write(vals)
    #     if 'to_agency' in vals:
    #         self.update_agency_line_account()
    #     return res


class AccountMoveLine(models.Model):
    '''inherit account.move.line'''

    _inherit = 'account.move.line'

    to_agency = fields.Boolean('A Agencia', related='move_id.to_agency')

    def _get_account_product(self):
        ''' return account product '''

        account_id = False
        if self.product_id:
            fiscal_position = self.move_id.fiscal_position_id
            accounts = self.with_company(self.company_id).product_id\
                .product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
            account_id = accounts['expense'] or self.account_id
        elif self.partner_id:
            account_id = self.env['account.account']._get_most_frequent_account_for_partner(
                company_id=self.company_id.id,
                partner_id=self.partner_id.id,
                move_type=self.move_id.move_type,
            )
        return account_id

    @api.depends('product_id', 'product_uom_id', 'move_id.to_agency')
    def _compute_tax_ids(self):
        product_lines = self.filtered(
            lambda l: l.display_type == 'product' and \
            not l.move_id.to_agency and \
            l.move_id.move_type in ['in_invoice', 'in_refund'])
        super(AccountMoveLine, self - product_lines)._compute_tax_ids()
        for line in product_lines:
            if line.tax_ids:
                line.tax_ids = [(6, 0, [])]
