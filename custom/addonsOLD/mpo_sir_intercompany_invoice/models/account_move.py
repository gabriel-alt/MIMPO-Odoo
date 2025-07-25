from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    intercom_expense_acc = fields.Boolean()

    @api.onchange('sir_id', 'intercom_expense_acc')
    def _onchange_sir_id(self):
        """ Set SIR on invoice line when update header SIR ID """
        if self.sir_id and not self.intercom_expense_acc:
            for line in self.invoice_line_ids:
                line.sir_id = self.sir_id.id
                analytic_distribution = {str(line.sir_id.account_analytic_id.id):100}
                line.analytic_distribution = analytic_distribution
        elif self.sir_id and self.intercom_expense_acc:
            for line in self.invoice_line_ids:
                if self.sir_id:
                    line.sir_id = self.sir_id.id
                analytic_distribution = line.analytic_distribution
                if self.sir_id.account_analytic_id and analytic_distribution and \
                    str(self.sir_id.account_analytic_id.id) in analytic_distribution:
                    del analytic_distribution[str(self.sir_id.account_analytic_id.id)]
                line.analytic_distribution = analytic_distribution

    # def _inter_company_prepare_invoice_data(self, invoice_type):
    #     """extend function for add several related SIR data """
    #     res = super(AccountMove, self)._inter_company_prepare_invoice_data(invoice_type)
    #     if not self.sir_id:
    #         return res
    #     if not self.intercom_expense_acc:
    #         res['to_agency'] = True
    #     res['sir_id'] = self.sir_id.id
    #     res['custom_house_id'] = self.custom_house_id and \
    #         self.custom_house_id.id or False
    #     res['sir_number'] = self.sir_number
    #     res['operation_type'] = self.operation_type
    #     res['pedimento'] = self.pedimento
    #     res['pedimento_date'] = self.pedimento_date
    #     res['pedimento_invoice'] = self.pedimento_invoice
    #     res['number_mark'] = self.number_mark
    #     res['ware'] = self.ware
    #     res['total_package'] = self.total_package
    #     res['reception'] = self.reception
    #     res['order_number'] = self.order_number
    #     res['custom_house'] = self.custom_house
    #     res['ship'] = self.ship
    #     res['supplier'] = self.supplier
    #     res['total_weight'] = self.total_weight
    #     return res


class AccountMoveLine(models.Model):
    """ Inherit Account Move Line """
    _inherit = 'account.move.line'

    @api.onchange('sir_id')
    def _onchange_sir_id(self):
        """ Set analytic_distribution on invoice line when change SIR """
        if self.sir_id and not self.move_id.intercom_expense_acc:
            analytic_distribution = {str(self.sir_id.account_analytic_id.id):100}
            self.analytic_distribution = analytic_distribution
