# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, _
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    expense_id = fields.Many2one(
        'hr.expense', 'Expense',
        help='Stores the expense related with this invoice')

    def l10n_mx_edi_expense_autopaid(self):
        """If the invoice is related with a expense with payment mode to the
        employee, automatically register the payment"""
        payment_obj = self.env['account.register.payments']
        for inv in self.filtered(
                lambda i: i.expense_id.payment_mode == 'own_account'):
            expense = inv.expense_id
            if not expense.employee_id.journal_id:
                raise ValidationError(_(
                    'The journal is required in the expense employee'))
            inv.action_invoice_open()
            ctx = {'active_model': 'account.invoice', 'active_ids': inv.ids}
            journal = expense.employee_id.journal_id
            payment_method = journal.outbound_payment_method_ids
            payment_obj.with_context(ctx).create({
                'payment_date': inv.date_invoice,
                'payment_method_id': payment_method[0].id if payment_method else False,  # noqa
                'journal_id': journal.id,
                'communication': expense.name,
                'amount': inv.amount_total,
            }).create_payment()
