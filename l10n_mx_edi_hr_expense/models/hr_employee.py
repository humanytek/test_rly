# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    journal_id = fields.Many2one(
        'account.journal', 'Journal', help='Specifies the journal that will '
        'be used to make the reimbursements to employees, for expenses with '
        'type "to reimburse"', domain=[('type', 'in', ['cash', 'bank'])])
