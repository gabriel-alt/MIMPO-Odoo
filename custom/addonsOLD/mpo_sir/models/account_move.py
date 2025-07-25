# -*- coding: utf-8 -*-
""" Account Move """
from odoo import models, fields, api

class AccountMove(models.Model):
    """ Inherit Account Move """

    _inherit = 'account.move'

    sir_id = fields.Many2one('sir.ref',string='Referencia SIR')
    downpayment_invoice = fields.Boolean()

    # @api.onchange('partner_id')
    # def _onchange_sir_id_domain(self):
    #     """ Set domain of SIR ID """

    #     for rec in self:
    #         domain = [('state', '=', 'open'), ('customer', '=', False)]
    #         if rec.partner_id.partner_ref:
    #             partner_ref = rec.partner_id.partner_ref
    #             domain =[('customer', '=', str(partner_ref)), ('state', '=', 'open')]
    #         return {'domain': {'sir_id': domain}}

    @api.onchange('sir_id')
    def _onchange_sir(self):
        """ Onchange SIR Reference """

        for move in self:
            if move.sir_id and move.sir_id.customer \
                    and move.move_type in ['out_invoice', 'out_refund']:
                partner = self.env['res.partner'].search_read(
                    domain=[('partner_ref', '=', move.sir_id.customer)], fields=['id'], limit=1)
                if partner:
                    move.update({'partner_id': partner[0].get('id')})

    def update_sir_reference_state(self):
        """ Update State of SIR Reference """

        state = 'open' if self._context.get('open_sir_reference') else 'close'
        filter_move = self
        if state == 'close':
            filter_move = self.filtered(lambda s: 'CGA' not in s.journal_id.code)
        if filter_move:
            sir_ref = filter_move.mapped('sir_id')
            # only update when necessary
            sir_ref.filtered(lambda r, s=state: r.state != s).write({'state': state})

    def _post(self, soft=True):
        """ Inherit Post """

        res = super(AccountMove, self)._post(soft=soft)
        # Change the SIR Ref's state into close
        self.filtered(lambda r: r.move_type == 'out_invoice' \
                      and not r.downpayment_invoice \
                      and r.state == 'posted' and r.sir_id).update_sir_reference_state()
        return res

    def button_cancel(self):
        """ Inherit Button Cancel """

        res = super(AccountMove, self).button_cancel()
        # Change the SIR Ref's state into open
        self.filtered(lambda r: r.sir_id).with_context(
            open_sir_reference=True).update_sir_reference_state()
        return res

    @api.model_create_multi
    def create(self, vals):
        moves = super(AccountMove, self).create(vals)
        if moves:
            close_sir_move = moves.filtered(
                lambda r: r.move_type == 'out_invoice' \
                and not r.downpayment_invoice and r.sir_id)
            if close_sir_move:
                close_sir_move.update_sir_reference_state()
            open_sir_move = moves - close_sir_move
            if open_sir_move:
                open_sir_move.with_context(
                    open_sir_reference=True).update_sir_reference_state()
        return moves

    def write(self, vals):
        if 'move_type' in vals or 'downpayment_invoice' in vals or \
            'sir_id' in vals:
            self.with_context(
                open_sir_reference=True).update_sir_reference_state()
        res = super(AccountMove, self).write(vals)
        if 'move_type' in vals or 'downpayment_invoice' in vals or \
            'sir_id' in vals:
            close_sir_move = self.filtered(
                lambda r: r.move_type == 'out_invoice' \
                and not r.downpayment_invoice and r.sir_id)
            if close_sir_move:
                close_sir_move.update_sir_reference_state()
        return res

class AccountMoveLine(models.Model):
    """ Inherit Account Move Line """

    _inherit = 'account.move.line'

    sir_id = fields.Many2one('sir.ref',string='Referencia SIR')
