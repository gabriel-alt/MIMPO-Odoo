"""Account Move"""

from odoo import models, fields, api, _
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import ValidationError
from odoo.addons.account_edi.models.account_move import AccountMove as OriginAccountMove
import logging

_logger = logging.getLogger(__name__)


def _prepare_edi_vals_to_export(self):
    """Monkey Patch Prepare EDI Vals to Export"""

    self.ensure_one()

    res = {
        "record": self,
        "balance_multiplicator": -1 if self.is_inbound() else 1,
        "invoice_line_vals_list": [],
    }

    # Invoice lines details.
    # CUSTOM: exclude CGA lines
    for index, line in enumerate(
        self.invoice_line_ids.filtered(lambda line: line.display_type == "product"),
        start=1,
    ):
        # and (not line.cga_line or line.origin_expense_line_id.to_agency)
        line_vals = line._prepare_edi_vals_to_export()
        line_vals["index"] = index
        res["invoice_line_vals_list"].append(line_vals)

    # Totals.
    res.update(
        {
            "total_price_subtotal_before_discount": sum(
                x["price_subtotal_before_discount"]
                for x in res["invoice_line_vals_list"]
            ),
            "total_price_discount": sum(
                x["price_discount"] for x in res["invoice_line_vals_list"]
            ),
        }
    )

    return res


OriginAccountMove._prepare_edi_vals_to_export = _prepare_edi_vals_to_export


class AccountMove(models.Model):
    """Inherit Account Move"""

    _inherit = "account.move"

    partner_expense_line_ids = fields.One2many(
        "account.move.line", "expense_move_id", string="Partner Expense", copy=False
    )
    total_expense = fields.Monetary(
        "Total Expense (Company Currency)",
        compute="_compute_expense_amount",
        store=True,
    )
    total_expense_currency = fields.Monetary(
        "Total Expense", compute="_compute_expense_amount", store=True
    )
    trusted_fund_balance = fields.Monetary(
        compute="_compute_trusted_fund_balance", store=True
    )
    remaining_trusted_fund_balance = fields.Monetary(
        compute="_compute_trusted_fund_balance", store=True
    )
    trusted_fund_statement_line_ids = fields.Many2many(
        "account.bank.statement.line",
        "account_move_trusted_fund_statement_line_rel",
        "move_id",
        "statement_line_id",
        compute="_compute_trusted_fund_balance",
        store=True,
    )
    invoice_expense_ids = fields.Many2many(
        "account.move",
        "invoice_expense_account_move_rel",
        "bill_id",
        "invoice_expense_id",
        compute="_compute_invoice_expense_ids",
    )
    l10n_mx_edi_payment_policy = fields.Selection(
        string="Payment Policy",
        selection=[("PPD", "PPD"), ("PUE", "PUE")],
        compute="_compute_l10n_mx_edi_payment_policy",
        readonly=False,
        store=True,
        inverse="_inverse_l10n_mx_edi_payment_policy",
    )
    l10n_mx_edi_payment_policy_draft = fields.Selection(
        string="Payment Policy Draft",
        selection=[("PPD", "PPD"), ("PUE", "PUE")],
        readonly=True,
    )

    @api.depends(
        "partner_id",
        "move_type",
        "invoice_date_due",
        "invoice_date",
        "invoice_payment_term_id",
        "invoice_payment_term_id.line_ids",
    )
    def _compute_l10n_mx_edi_payment_policy(self):
        non_draft = self.env["account.move"]
        for move in self:
            if not move.l10n_mx_edi_payment_policy_draft:
                non_draft |= move
            else:
                move.l10n_mx_edi_payment_policy = move.l10n_mx_edi_payment_policy_draft
        super(AccountMove, non_draft)._compute_l10n_mx_edi_payment_policy()
        for move in non_draft:
            if (
                move.is_invoice(include_receipts=True)
                and move.partner_id
                and move.partner_id.l10n_mx_edi_payment_policy
            ):
                move.l10n_mx_edi_payment_policy = (
                    move.partner_id.l10n_mx_edi_payment_policy
                )

    def _inverse_l10n_mx_edi_payment_policy(self):
        for move in self:
            if move.l10n_mx_edi_payment_policy_draft != move.l10n_mx_edi_payment_policy:
                move.l10n_mx_edi_payment_policy_draft = move.l10n_mx_edi_payment_policy

    @api.depends("invoice_line_ids.expense_move_id")
    def _compute_invoice_expense_ids(self):
        for move in self:
            move_ids = move.invoice_line_ids.mapped("expense_move_id")
            move.update(
                {"invoice_expense_ids": [(6, 0, move_ids and move_ids.ids or [])]}
            )

    @api.depends(
        "partner_expense_line_ids",
        "partner_expense_line_ids.total_expense",
        "partner_expense_line_ids.subtotal_expense_currency",
    )

    # En esta función se calcula el total de gastos efectuados por cuenta del cliente e ignora los que sean to_agency
    def _compute_expense_amount(self):
        """Compute Expense Amount"""

        for move in self:
            total_expense = 0.0
            total_expense_currency = 0.0
            for line in move.partner_expense_line_ids:
                # total_expense_currency += line.subtotal_expense_currency
                if not line.to_agency:
                    total_expense += line.subtotal_expense
                    total_expense_currency += line.subtotal_expense_currency
            move.update(
                {
                    "total_expense": total_expense,
                    "total_expense_currency": total_expense_currency,
                }
            )

    @api.depends(
        "sir_id",
        "date",
        "total_expense",
        "amount_total",
        "state",
        "currency_id",
        "total_expense_currency",
    )
    def _compute_trusted_fund_balance(self):
        """Compute Balance of trusted fund amount"""

        for move in self:
            tf_line = self.env["account.bank.statement.line"].sudo()
            tr_bal = 0.0
            if (
                move.sir_id
                and move.state != "cancel"
                and move.move_type in ("out_invoice", "out_refund")
            ):
                domain = [
                    ("sir_id", "=", move.sir_id.id),
                    ("move_id.company_id", "=", move.company_id.id),
                ]
                st_line = self.env["account.bank.statement.line"].sudo().search(domain)
                for line in st_line:
                    # skip if bank statement already linked to other invoice
                    if (
                        line.trusted_fund_move_ids
                        and line.trusted_fund_move_ids.filtered(
                            lambda r, m=move: r.state != "cancel" and r != m._origin
                        )
                    ):
                        continue
                    # skip non trusted account
                    if all(
                        not sl.account_id.trust_fund for sl in line.move_id.line_ids
                    ):
                        continue
                    tf_line |= line
                    if line.currency_id != move.currency_id:
                        rate = self.env["res.currency"]._get_conversion_rate(
                            from_currency=line.currency_id,
                            to_currency=move.currency_id,
                            company=move.company_id,
                            date=move.invoice_date
                            or move.date
                            or fields.Date.context_today(line),
                        )
                        tr_bal += abs(move.currency_id.round(line.amount / rate))
                    else:
                        tr_bal += abs(line.amount)
            # remaining = tr_bal - sum(move.invoice_line_ids.filtered(
            #     lambda r: not r.cga_line and r.display_type == 'product').mapped('price_total'))
            move.update(
                {
                    "remaining_trusted_fund_balance": move.currency_id.round(
                        tr_bal - move.total_expense_currency
                    ),
                    "trusted_fund_balance": tr_bal,
                    "trusted_fund_statement_line_ids": [(6, 0, tf_line.ids)],
                }
            )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        super()._onchange_partner_id()
        if self.partner_id and self.partner_id.l10n_mx_edi_usage:
            self.l10n_mx_edi_usage = self.partner_id.l10n_mx_edi_usage

    def _search_default_journal(self):
        """Inherit Search Default Journal"""

        # bypass journal switch on CGA type switch confirmation
        if self._context.get("switch_type_cga"):
            return self.journal_id
        return super()._search_default_journal()

    def _get_new_expense_items(self, type_sign=1):
        return []

    def generate_cga_expense_entries(self):
        """Generate CGA entries"""

        items = []
        # remove existing expenses if any
        for line in self.line_ids.filtered(lambda r: r.cga_line):
            items.append((2, line.id))

        # Determine type sign for conditional switching move type
        # balance = sum(self.partner_expense_line_ids.mapped('balance')) \
        #     + -1 * sum(self.line_ids.filtered(
        #     lambda r: not r.cga_line and r.display_type in [
        #         'product', 'tax', 'rounding']).mapped('balance')) \
        #     - self.trusted_fund_balance
        # type_sign = 1 if float_compare(
        #     balance, 0.0, precision_rounding=self.currency_id.rounding) >= 0 else -1
        fund_balance = self.trusted_fund_balance
        for line in self.partner_expense_line_ids:
            fund_balance -= line.subtotal_expense_currency
        type_sign = (
            1
            if float_compare(
                fund_balance, 0.0, precision_rounding=self.currency_id.rounding
            )
            <= 0
            else -1
        )

        # Expense Lines
        vals_list = []
        for line in self.partner_expense_line_ids:
            price = line.price_unit
            balance = line.balance
            taxes = (
                line.product_id.with_company(self.company_id).taxes_id.ids
                if line.product_id and line.move_id.to_agency
                else []
            )

            # define account
            if line.move_id.to_agency and line.product_id:
                accounts = line.with_company(
                    line.company_id
                ).product_id.product_tmpl_id.get_product_accounts(
                    fiscal_pos=self.fiscal_position_id
                )
                account = (
                    accounts["income"].id if accounts.get("income") else line.account_id
                )
            elif line.move_id.to_agency and self.partner_id:
                account = self.env[
                    "account.account"
                ]._get_most_frequent_account_for_partner(
                    company_id=self.company_id.id,
                    partner_id=self.partner_id.id,
                    move_type=self.move_type,
                )
            else:
                account = line.account_id.id

            if line.currency_id != self.currency_id:
                # price = line.currency_id.round(line.subtotal_expense / line.quantity)
                balance = line.subtotal_expense
                price = line.currency_id.with_context(
                    from_bill_line=line, to_expense_move=self
                )._convert(
                    from_amount=line.price_unit,
                    to_currency=self.currency_id,
                    company=self.company_id,
                    date=self.invoice_date
                    or self.date
                    or fields.Date.context_today(self),
                )
            same_data = False
            for vl in vals_list:
                line_name = line.expense_description or line.name
                if (
                    account != vl.get("account_id")
                    or line_name != vl.get("name")
                    or line.quantity != vl.get("quantity")
                    or line.discount != vl.get("discount")
                ):
                    continue
                if line.move_id.to_agency and not vl.get("to_agency"):
                    continue
                if not line.move_id.to_agency and vl.get("to_agency"):
                    continue
                # if not line.move_id.to_agency:
                #     vl['product_id'] = False
                vl["origin_expense_line_id"] = False
                new_origin = []
                if vl.get("origin_expense_line_ids"):
                    new_origin = vl["origin_expense_line_ids"][0][2]
                new_origin.append(line.id)
                vl["origin_expense_line_ids"] = [(6, 0, new_origin)]
                vl["price_unit"] += type_sign * price
                same_data = True
            if not same_data:
                vals = {
                    "account_id": account,
                    "product_id": line.product_id.id,  # if line.move_id.to_agency else False,
                    "to_agency": line.move_id.to_agency,
                    "discount": line.discount,
                    "name": line.expense_description or line.name,
                    "partner_id": self.partner_id.id,
                    "quantity": line.quantity,
                    "analytic_distribution": line.analytic_distribution,
                    "price_unit": type_sign * price,
                    # 'debit': type_sign * line.company_id.currency_id.round(
                    #     line.credit / line.exchange_rate),
                    # 'credit': type_sign * line.company_id.currency_id.round(
                    #     line.debit / line.exchange_rate),
                    "tax_ids": [(6, 0, taxes)],
                    # 'balance': self.currency_id.round(type_sign * -1 * balance),
                    "currency_id": self.currency_id.id,
                    # 'amount_currency': self.currency_id.round(type_sign * -1 * balance),
                    "origin_expense_line_id": line.id,
                    "origin_expense_line_ids": [(6, 0, [line.id])],
                    "sir_id": self.sir_id.id,
                    "cga_line": True,
                    "display_type": "product",
                }
                vals_list.append(vals)
        for vals in vals_list:
            items.append((0, 0, vals))

        # Trusted Fund Line
        tr_bal = 0.0
        for move in self.trusted_fund_statement_line_ids.mapped("move_id"):
            tf_move = move.line_ids.filtered(lambda r: r.account_id.trust_fund)
            if not tf_move:
                msg = (
                    "Please define account for trust fund in "
                    f"the bank stamement line {move.statement_line_id.payment_ref}"
                )
                raise ValidationError(_(msg))
            exp_amount = 0.0
            for line in tf_move:
                if line.currency_id != self.currency_id:
                    rate = self.env["res.currency"]._get_conversion_rate(
                        from_currency=line.currency_id,
                        to_currency=self.currency_id,
                        company=move.company_id,
                        date=self.invoice_date
                        or self.date
                        or fields.Date.context_today(line),
                    )
                    tr_bal = self.currency_id.round(line.amount_currency / rate)
                else:
                    tr_bal = line.amount_currency
                exp_amount = line.amount_currency
            tf_line = {
                "account_id": line.account_id.id,
                "trust_fund_account_id": line.account_id.id,
                "name": line.name,
                "partner_id": self.partner_id.id,
                "analytic_distribution": {str(self.sir_id.account_analytic_id.id): 100},
                "quantity": 1.0,
                "price_unit": type_sign * tr_bal,
                "tax_ids": [(6, 0, [])],
                #    'debit': -1 * tr_bal,
                #    'credit': 0.0,
                "balance": type_sign * -1 * tr_bal,
                "currency_id": self.currency_id.id,
                "amount_currency": type_sign * -1 * tr_bal,
                "expense_bill_currency_id": move.currency_id.id,
                "expense_amount_currency": type_sign * -1 * exp_amount,
                "cga_line": True,
                #    'display_type': 'product'
            }
            items.append((0, 0, tf_line))
        new_items = self._get_new_expense_items(type_sign=type_sign)
        for ni in new_items:
            items.append(ni)
        if items:
            vals = {"line_ids": items}
            if type_sign < 0:
                vals["move_type"] = "out_refund"
            switch_type = True if "move_type" in vals else False
            self.with_context(switch_type_cga=switch_type).write(vals)
            bal_update = []
            for line in self.invoice_line_ids.filtered(lambda r: r.cga_line):
                if line.currency_id != self.company_id.currency_id:
                    total_balance = 0
                    for org_line in line.origin_expense_line_ids:
                        total_balance += org_line.balance
                    if abs(line.balance) != abs(total_balance):
                        if line.credit > 0:
                            bal_update.append(
                                (
                                    1,
                                    line.id,
                                    {
                                        "balance": -1 * total_balance,
                                        "credit": total_balance,
                                    },
                                )
                            )
                        else:
                            bal_update.append(
                                (
                                    1,
                                    line.id,
                                    {"balance": total_balance, "debit": total_balance},
                                )
                            )
            if bal_update:
                self.with_context(switch_type_cga=switch_type).write(
                    {"line_ids": bal_update}
                )
        # Journal correction
        ln_vals = []
        for line in self.invoice_line_ids.filtered(lambda r: r.cga_line):
            if (
                line.origin_expense_line_id
                and not line.origin_expense_line_id.move_id.to_agency
                and line.origin_expense_line_id.account_id != line.account_id
            ):
                ln_vals.append(
                    (
                        1,
                        line.id,
                        {"account_id": line.origin_expense_line_id.account_id.id},
                    )
                )
            elif (
                line.trust_fund_account_id
                and line.trust_fund_account_id != line.account_id
            ):
                ln_vals.append(
                    (1, line.id, {"account_id": line.trust_fund_account_id.id})
                )

        # Currency rounding correction
        diff = 0.0
        for line in self.invoice_line_ids.filtered(
            lambda r: r.origin_expense_line_id
            and float_compare(
                r.origin_expense_line_id.currency_rate,
                r.origin_expense_line_id.exchange_rate,
                precision_rounding=self.currency_id.rounding,
            )
            != 0
            and float_compare(
                abs(r.balance),
                abs(r.origin_expense_line_id.balance),
                precision_rounding=self.currency_id.rounding,
            )
            != 0
        ):
            diff += abs(line.origin_expense_line_id.balance) - abs(line.balance)
        if not float_is_zero(diff, precision_rounding=self.currency_id.rounding):
            income_exchange_account = (
                self.company_id.income_currency_exchange_account_id
            )
            vals = {
                "name": _("Currency exchange rate difference"),
                "analytic_distribution": {str(self.sir_id.account_analytic_id.id): 100},
                "quantity": 1.0,
                "price_unit": type_sign * diff,
                "balance": type_sign * -1 * diff,
                "tax_ids": [(6, 0, [])],
                "amount_currency": type_sign * -1 * diff,
                "account_id": income_exchange_account.id,
                "partner_id": self.partner_id.id,
                "sequence": len(self.line_ids) + 1,
                "move_type": "rounding",
                "cga_line": True,
            }
            ln_vals.append((0, 0, vals))

        if ln_vals:
            self.write({"line_ids": ln_vals})

    def action_link_expense(self):
        """Link Expense to Invoice"""

        self.ensure_one()
        if not self.sir_id:
            return
        domain = [
            ("sir_id", "=", self.sir_id.id),
            ("expense_move_id", "=", False),
            ("move_id.state", "=", "posted"),
            ("move_type", "=", "in_invoice"),
            ("product_id.concepto_corresponsal", "=", False),
            ("display_type", "=", "product"),
        ]
        bill_lines = self.env["account.move.line"].search(domain)
        if not bill_lines:
            msg = _(
                "There are no published documents for reference SIR %s"
                " or were already used in a previous invoice",
                self.sir_id.number,
            )
            raise ValidationError(msg)
        bill_lines.write({"expense_move_id": self.id})
        if self.move_type == "out_invoice" and bill_lines:
            self.generate_cga_expense_entries()
            self._compute_tax_totals()

    def _post(self, soft=True):
        """Inherit Post"""

        # for move in self.filtered(
        #         lambda r: r.move_type == 'out_invoice' and r.partner_expense_line_ids):
        #     move.generate_cga_expense_entries()
        res = super(AccountMove, self)._post(soft=soft)
        return res

    def unlink_partner_expense(self):
        """Remove Link for Customer Expense"""

        self.write({"partner_expense_line_ids": [(5,)]})

    def button_cancel(self):
        """Inherit Button Cancel"""

        res = super(AccountMove, self).button_cancel()
        self.filtered(lambda r: r.partner_expense_line_ids).unlink_partner_expense()
        return res

    def _prepare_invoice_aggregated_taxes(
        self,
        filter_invl_to_apply=None,
        filter_tax_values_to_apply=None,
        grouping_key_generator=None,
    ):
        """Conditional Replace Prepare Invoice Aggravated Taxes"""

        self.ensure_one()
        if not self._context.get("mx_edi"):
            return super(AccountMove, self)._prepare_invoice_aggregated_taxes(
                filter_invl_to_apply=filter_invl_to_apply,
                filter_tax_values_to_apply=filter_tax_values_to_apply,
                grouping_key_generator=None,
            )

        # CUSTOM: conditional replace exclude CGA Lines
        base_lines = [
            x._convert_to_tax_base_line_dict()
            for x in self.line_ids.filtered(
                lambda x: (not x.cga_line or (x.cga_line and x.product_id))
                and x.display_type == "product"
                and (not filter_invl_to_apply or filter_invl_to_apply(x))
            )
        ]

        to_process = []
        for base_line in base_lines:
            to_update_vals, tax_values_list = self.env[
                "account.tax"
            ]._compute_taxes_for_single_line(base_line)
            to_process.append((base_line, to_update_vals, tax_values_list))

        return self.env["account.tax"]._aggregate_taxes(
            to_process,
            filter_tax_values_to_apply=filter_tax_values_to_apply,
            grouping_key_generator=grouping_key_generator,
        )


class AccountMoveLine(models.Model):
    """Inherit Account Move Line"""

    _inherit = "account.move.line"

    expense_move_id = fields.Many2one("account.move", ondelete="set null", copy=False)
    exchange_rate = fields.Float(
        "Tipo de cambio", compute="_compute_exchange_rate", store=True, readonly=False
    )
    total_expense = fields.Monetary(
        "Total Expense",
        compute="_compute_expense_amount",
        currency_field="company_currency_id",
        store=True,
    )
    subtotal_expense = fields.Monetary(
        "Subtotal Expense (company currency)",
        compute="_compute_expense_amount",
        currency_field="company_currency_id",
        store=True,
    )
    expense_move_currency_id = fields.Many2one(
        "res.currency",
        string="Expense Move Currency",
        compute="_compute_expense_move_currency_id",
        readonly=True,
        store=True,
        precompute=True,
    )
    total_expense_currency = fields.Monetary(
        "Total Expense Currency",
        compute="_compute_expense_price_move_currency_id",
        currency_field="expense_move_currency_id",
        store=True,
    )
    subtotal_expense_currency = fields.Monetary(
        "Subtotal Expense",
        compute="_compute_expense_price_move_currency_id",
        currency_field="expense_move_currency_id",
        store=True,
    )
    price_unit_expense_currency = fields.Float(
        string="Expense Unit Price",
        compute="_compute_expense_price_move_currency_id",
        store=True,
        currency_field="expense_move_currency_id",
    )
    origin_expense_line_id = fields.Many2one("account.move.line", ondelete="set null")
    origin_expense_line_ids = fields.Many2many(
        "account.move.line",
        "origin_expense_account_move_line_rel",
        "inv_line_id",
        "bill_line_id",
        copy=False,
        readonly=True,
    )
    invoice_expense_line_ids = fields.Many2many(
        "account.move.line",
        "origin_expense_account_move_line_rel",
        "bill_line_id",
        "inv_line_id",
        copy=False,
        readonly=True,
    )
    cga_line = fields.Boolean(
        help="Line Generated from CGA Operation", copy=False, readonly=True
    )
    to_agency = fields.Boolean(
        help="To Agency from CGA Operation", copy=False, readonly=True
    )
    trust_fund_account_id = fields.Many2one("account.account")
    expense_price_unit = fields.Float(
        string="Expense Unit Price (Bills)",
        compute="_compute_expense_price_unit",
        store=True,
        readonly=False,
        precompute=True,
        digits="Product Price",
    )
    expense_description = fields.Char(
        string="Expense Description",
        compute="_compute_expense_description",
        store=True,
        readonly=False,
        precompute=True,
    )
    expense_bill_currency_id = fields.Many2one(
        "res.currency",
        string="Expense Bill Currency",
        compute="_compute_expense_bill_currency_id",
        store=True,
        readonly=False,
        precompute=True,
    )
    expense_amount_currency = fields.Monetary(
        string="Expense Amount Currency",
        compute="_compute_expense_amount_currency",
        currency_field="expense_bill_currency_id",
        store=True,
        readonly=False,
        precompute=True,
    )

    @api.depends("origin_expense_line_ids", "currency_id")
    def _compute_expense_bill_currency_id(self):
        for line in self:
            cur_id = line.currency_id
            if (
                line.origin_expense_line_ids
                and line.origin_expense_line_ids[0].currency_id != line.currency_id
            ):
                cur_id = line.origin_expense_line_ids[0].currency_id
            line.update({"expense_bill_currency_id": cur_id.id})

    @api.depends(
        "origin_expense_line_ids",
        "expense_bill_currency_id",
        "display_type",
        "amount_currency",
    )
    def _compute_expense_amount_currency(self):
        for line in self:
            amount_cur = 0.0
            if line.display_type != "product":
                amount_cur = line.amount_currency
            elif line.origin_expense_line_ids:
                for oel in line.origin_expense_line_ids:
                    if oel.currency_id != line.expense_bill_currency_id:
                        amount_cur += oel.currency_id._convert(
                            from_amount=oel.amount_currency,
                            to_currency=line.expense_bill_currency_id,
                            company=line.move_id.company_id,
                            date=line.move_id.invoice_date
                            or line.move_id.date
                            or fields.Date.context_today(self),
                        )
                    else:
                        amount_cur += oel.amount_currency
            elif line.expense_bill_currency_id != line.currency_id:
                amount_cur = line.currency_id._convert(
                    from_amount=line.amount_currency,
                    to_currency=line.expense_bill_currency_id,
                    company=line.move_id.company_id,
                    date=line.move_id.invoice_date
                    or line.move_id.date
                    or fields.Date.context_today(self),
                )
            else:
                amount_cur = line.amount_currency
            line.update({"expense_amount_currency": amount_cur})

    @api.depends("expense_move_id", "expense_move_id.currency_id")
    def _compute_expense_move_currency_id(self):
        for line in self:
            expense_move_currency_id = line.currency_id
            if line.expense_move_id.currency_id != line.currency_id:
                expense_move_currency_id = line.expense_move_id.currency_id
            line.update({"expense_move_currency_id": expense_move_currency_id.id})

    @api.depends(
        "expense_move_id",
        "expense_move_currency_id",
        "expense_move_id.invoice_date",
        "price_total",
        "price_subtotal",
    )
    def _compute_expense_price_move_currency_id(self):
        """Compute Expense Move Currency ID"""
        for line in self:
            if not line.expense_move_id or not line.expense_move_currency_id:
                line.update(
                    {
                        "price_unit_expense_currency": line.price_unit,
                        "total_expense_currency": line.price_total,
                        "subtotal_expense_currency": line.price_subtotal,
                    }
                )
                continue
            expense_move_currency_id = line.expense_move_currency_id or line.currency_id
            price_unit_expense_currency = line.price_unit
            total_expense_currency = line.price_total
            subtotal_expense_currency = line.price_subtotal
            if expense_move_currency_id != line.currency_id:
                price_unit_expense_currency = line.currency_id._convert(
                    from_amount=line.price_unit,
                    to_currency=expense_move_currency_id,
                    company=line.expense_move_id.company_id,
                    date=line.expense_move_id.invoice_date
                    or line.expense_move_id.date
                    or fields.Date.context_today(line),
                )
                total_expense_currency = line.currency_id._convert(
                    from_amount=line.price_total,
                    to_currency=expense_move_currency_id,
                    company=line.expense_move_id.company_id,
                    date=line.expense_move_id.invoice_date
                    or line.expense_move_id.date
                    or fields.Date.context_today(line),
                )
                subtotal_expense_currency = line.currency_id._convert(
                    from_amount=line.price_subtotal,
                    to_currency=expense_move_currency_id,
                    company=line.expense_move_id.company_id,
                    date=line.expense_move_id.invoice_date
                    or line.expense_move_id.date
                    or fields.Date.context_today(line),
                )
            line.update(
                {
                    "price_unit_expense_currency": price_unit_expense_currency,
                    "total_expense_currency": total_expense_currency,
                    "subtotal_expense_currency": subtotal_expense_currency,
                }
            )

    @api.depends("is_same_currency")
    def _compute_exchange_rate(self):
        """Compute Exchange Rate"""

        for line in self:
            line.exchange_rate = 1.0 if line.is_same_currency else line.currency_rate

    @api.depends("exchange_rate", "price_total", "price_subtotal")
    def _compute_expense_amount(self):
        """Compute Expense Amount"""

        for line in self:
            total_expense = line.price_total
            subtotal_expense = line.price_subtotal
            if (
                line.expense_move_id
                and line.currency_id != line.expense_move_id.currency_id
            ):
                total_expense = line.expense_move_id.currency_id.round(
                    total_expense / line.exchange_rate
                )
                subtotal_expense = line.expense_move_id.currency_id.round(
                    subtotal_expense / line.exchange_rate
                )
            line.update(
                {"total_expense": total_expense, "subtotal_expense": subtotal_expense}
            )

    @api.depends("price_unit", "expense_move_id.currency_id", "currency_id")
    def _compute_expense_price_unit(self):
        """Compute Expense Price Unit"""
        for line in self:
            price_unit = line.price_unit
            if (
                line.expense_move_id
                and line.currency_id != line.expense_move_id.currency_id
            ):
                exchange_rate = 1.0 if line.is_same_currency else line.currency_rate
                price_unit = line.expense_move_id.currency_id.round(
                    price_unit / exchange_rate
                )
            line.expense_price_unit = price_unit

    @api.depends("name")
    def _compute_expense_description(self):
        """Compute Expense Description"""
        for line in self:
            line.expense_description = line.name

    def _compute_account_id(self):
        """Extend Function for improve account expense"""
        super(AccountMoveLine, self)._compute_account_id()
        product_lines = self.filtered(
            lambda l: l.display_type == "product"
            and not l.move_id.to_agency
            and l.move_id.sir_id
            and l.move_id.move_type in ["in_invoice", "in_refund"]
        )
        for line in product_lines:
            if not line.move_id.company_id:
                continue
            customer_id = line.move_id.sir_id.partner_id
            # if not customer_id and line.move_id.sir_id.customer:
            #     customer_id = self.env['res.partner'].search([(
            #         'partner_ref', '=', line.move_id.sir_id.customer)])
            if customer_id:
                customer_id = customer_id.with_company(line.move_id.company_id)
                if customer_id.property_account_expense_partner_id:
                    line.account_id = customer_id.property_account_expense_partner_id
                elif line.move_id.journal_id.default_account_id:
                    line.account_id = line.move_id.journal_id.default_account_id
        cga_lines = self.filtered(
            lambda l: l.display_type == "product"
            and l.move_id.sir_id
            and l.cga_line
            and l.move_id.move_type in ["out_invoice", "out_refund"]
        )
        for cl in cga_lines:
            if not cl.origin_expense_line_ids and not cl.trust_fund_account_id:
                continue
            if (
                cl.origin_expense_line_id
                and not cl.origin_expense_line_id.move_id.to_agency
                and cl.origin_expense_line_id.account_id != cl.account_id
            ):
                cl.account_id = cl.origin_expense_line_id.account_id
            elif (
                cl.origin_expense_line_ids
                and not cl.origin_expense_line_ids[0].move_id.to_agency
                and cl.origin_expense_line_ids[0].account_id != cl.account_id
            ):
                cl.account_id = cl.origin_expense_line_ids[0].account_id
            elif cl.trust_fund_account_id and cl.trust_fund_account_id != cl.account_id:
                cl.account_id = cl.trust_fund_account_id
