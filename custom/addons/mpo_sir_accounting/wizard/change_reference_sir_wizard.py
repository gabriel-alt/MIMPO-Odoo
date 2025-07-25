# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from odoo import api, fields, models, _
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class ChangeReferenceSirWizard(models.TransientModel):
	_name = 'change.reference.sir.wizard'
	_description = 'Change Reference SIR Wizard'

	move_id = fields.Many2one(
        'account.move', string="Journal Entry")
	sir_id = fields.Many2one(
		'sir.ref',string='Old Referencia SIR', related='move_id.sir_id')
	change_reason = fields.Char()
	new_sir_id = fields.Many2one(
		'sir.ref',string='New Referencia SIR')

	def action_change_reference_sir(self):
		self.ensure_one()
		if not self.move_id:
			raise UserError(_("Cannot find the data, please refresh"))
		if not self.new_sir_id or not self.change_reason:
			raise UserError(_("Please set New Reference SIR and Change Reason"))
		msg = _('Change SIR : %s -> %s ',
			self.move_id.sir_id._get_html_link(), self.new_sir_id._get_html_link())
		msg += _(' <br/>Reason : %s', self.change_reason)
		self.move_id.write({'sir_id': self.new_sir_id.id})
		self.move_id.invoice_line_ids.write({'sir_id': self.new_sir_id.id})
		self.move_id._onchange_sir_id()
		self.move_id.message_post(body=_(msg))
		reconciled_partials = self.move_id._get_all_reconciled_invoice_partials()
		for recon in reconciled_partials:
			if recon.get('aml'):
				aml_id = recon.get('aml')
				if aml_id.move_id:
					aml_id.move_id.write({'sir_id': self.new_sir_id.id})
					aml_id.move_id.invoice_line_ids.write(
						{'sir_id': self.new_sir_id.id})
					aml_id.move_id._onchange_sir_id()
					aml_id.move_id.message_post(body=_(msg))
		return True
