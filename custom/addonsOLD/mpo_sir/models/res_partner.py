# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_ref = fields.Char(string='Clave del cliente')
    commercial_name = fields.Char(string="Nombre Comercial")

    @api.model_create_multi
    def create(self, vals):
        partners = super(ResPartner, self).create(vals)
        if not self.env.context.get('show_user_group_warning') and partners and any(
            not p.parent_id and not p.bank_ids and not p.user_ids for p in partners.with_context(active_test=False)):
            raise UserError(_("Please set Bank Account."))
        for this in partners:
            if this.partner_ref:
                this.process_account_partner_ref()
        return partners

    def write(self, vals):
        old_partner_ref = {}
        if vals.get('partner_ref'):
            for this in self:
                if this.partner_ref:
                    old_partner_ref[this.id] = this.partner_ref
        res = super(ResPartner, self).write(vals)
        if not self.env.context.get('show_user_group_warning') and self and any(
            not p.parent_id and not p.bank_ids and not p.user_ids for p in self.with_context(active_test=False)):
            raise UserError(_("Please set Bank Account."))
        if vals.get('partner_ref'):
            for this in self:
                this.process_account_partner_ref(old_ref=old_partner_ref)
        return res

    def process_create_account(
            self, com_id=0, type='asset_current', code=''):
        if not code:
            return False
        if not com_id:
            com_id = self.env.company.id
        return self.env['account.account'].create({
            'name': self.commercial_name or self.name,
            'code': code,
            'account_type': type, 'company_id': com_id
        })

    def process_search_account(
            self, com_id=0, type='asset_current', code=''):
        if not code:
            return False
        query = """
            SELECT id from account_account
            WHERE code=%s AND account_type=%s AND company_id=%s
        """
        params = (code, type, com_id)
        self._cr.execute(query, params)
        res = self._cr.fetchone()
        return res and res[0] or False

    def get_vals_account_partner_ref(self, company_ids):
        account_vals = {}
        for com in company_ids:
            account_vals[com.id] = {}
            ar_id = self.process_search_account(
                com_id=com.id, type='asset_receivable',
                code='105.01.'+ self.partner_ref + '.00')
            if not ar_id:
                ar_id = self.process_create_account(
                    com_id=com.id, type='asset_receivable',
                    code='105.01.'+ self.partner_ref + '.00')
                if ar_id:
                    account_vals[com.id][
                        'property_account_receivable_id'] = ar_id.id
            elif ar_id and ar_id != self.with_company(
                com).property_account_receivable_id.id:
                account_vals[com.id][
                    'property_account_receivable_id'] = ar_id
        return account_vals

    def process_account_partner_ref(self, old_ref={}):
        self.ensure_one()
        self = self.sudo()
        if not self.partner_ref:
            return False
        company_ids = self.env['res.company'].search([])
        account_vals = self.get_vals_account_partner_ref(company_ids)
        if account_vals:
            for com in company_ids:
                if com.id not in account_vals or \
                    not account_vals.get(com.id):
                    continue
                self.with_company(com).write(account_vals.get(com.id))
