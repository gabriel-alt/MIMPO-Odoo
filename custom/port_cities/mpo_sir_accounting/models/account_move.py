""" Account Move """
from odoo import api, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    """ Inherit Account Move """
    _inherit = 'account.move'

    @api.onchange('sir_id')
    def _onchange_sir_id(self):
        """ Set SIR on invoice line when update header SIR ID """
        if self.sir_id:
            for line in self.invoice_line_ids:
                line.sir_id = self.sir_id.id
                analytic_distribution = {str(line.sir_id.account_analytic_id.id):100}
                line.analytic_distribution = analytic_distribution

    def action_change_sir_ref(self):
        self.ensure_one()
        if not self[0].sir_id:
            raise UserError(_("Cannot find the Reference SIR"))
        ctx = dict(self.env.context.copy())
        ctx['default_move_id'] = self[0].id
        ctx['default_new_sir_id'] = self[0].sir_id.id
        return {
            'name': _('Change Reference SIR'),
            'view_mode': 'form',
            'res_model': 'change.reference.sir.wizard',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'new'}

    def action_register_payment(self):
        res = super(AccountMove, self).action_register_payment()
        if len(self.ids) == 1 and self[0].move_type == 'in_invoice' and \
            len(self[0].invoice_line_ids.mapped('sir_id')) >= 2:
            res['context']['default_bill_multi_sir'] = True
            # sir_lines = {}
            # for line in self[0].invoice_line_ids:
            #     if line.sir_id:
            #         if line.sir_id.id in sir_lines:
            #             sir_lines[line.sir_id.id][
            #                 'amount'] += line.price_total
            #             sir_lines[line.sir_id.id][
            #                 'sir_line_ids'][0][2].append(line.id)
            #         else:
            #             sir_lines[line.sir_id.id] = {
            #                 'sir_id': line.sir_id.id,
            #                 'sir_line_ids': [(6, 0, line.ids)],
            #                 'amount' : line.price_total
            #             }
            #     elif line.move_id.sir_id:
            #         if line.move_id.sir_id.id in sir_lines:
            #             sir_lines[line.move_id.sir_id.id][
            #                 'amount'] += line.price_total
            #             sir_lines[line.move_id.sir_id.id][
            #                 'sir_line_ids'][0][2].append(line.id)
            #         else:
            #             sir_lines[line.move_id.sir_id.id] = {
            #                 'sir_id': line.move_id.sir_id.id,
            #                 'sir_line_ids': [(6, 0, line.ids)],
            #                 'amount' : line.price_total
            #             }
            # pay_reg_sir_ids = []
            # for k, v in sir_lines.items():
            #     pay_reg_sir_ids.append((0, 0, v))
            # res['context']['default_pay_reg_sir_ids'] = pay_reg_sir_ids
        return res


class AccountMoveLine(models.Model):
    """ Inherit Account Move Line """
    _inherit = 'account.move.line'

    @api.onchange('sir_id')
    def _onchange_sir_id(self):
        """ Set analytic_distribution on invoice line when change SIR """
        if self.sir_id:
            analytic_distribution = {str(self.sir_id.account_analytic_id.id):100}
            self.analytic_distribution = analytic_distribution
