# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import os
from lxml.objectify import fromstring

from odoo.tools import misc
from odoo.tests.common import TransactionCase


class EdiHrExpense(TransactionCase):
    def setUp(self):
        super(EdiHrExpense, self).setUp()
        self.invoice_obj = self.env['account.invoice']
        self.product = self.env.ref('hr_expense.product_product_fixed_cost')
        self.employee = self.env.ref('hr.employee_root')
        self.xml_signed = misc.file_open(os.path.join(
            'l10n_mx_edi_hr_expense', 'tests', 'INV-INV20180035-MX-3-3.xml'),
            'r').read()
        account = self.env['account.account'].create({
            'code': '601.01.100',
            'name': 'Sueldos y salarios',
            'user_type_id': self.ref('account.data_account_type_payable'),
            'reconcile': True,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Expense Pieter',
            'type': 'cash',
            'code': 'EP',
            'default_debit_account_id': account.id,
            'default_credit_account_id': account.id,
        })
        self.employee.journal_id = self.journal

    def test_expense_cfdi(self):
        self.env.ref('base.MXN').active = False
        # Test without currency
        expense = self.create_expense()
        expense.company_id.vat = fromstring(
            self.xml_signed).Receptor.get('Rfc')
        self.create_attachment(expense.id)
        sheet = expense.sheet_id.with_context(
            expense.submit_expenses()['context']).create({})
        sheet.approve_expense_sheets()
        message = sheet.message_ids.mapped('body')
        self.assertTrue('The currency' in ''.join(message), message)

        self.env.ref('base.MXN').active = True
        # Test with bad company VAT
        expense = self.create_expense()
        expense.company_id.vat = 'XXX030303XX1'
        self.create_attachment(expense.id)
        sheet = expense.sheet_id.with_context(
            expense.submit_expenses()['context']).create({})
        sheet.approve_expense_sheets()
        message = sheet.message_ids.mapped('body')
        self.assertTrue("Receptor's RFC in the XML does not match" in ''.join(
            message), message)

        # Test Correct case
        expense = self.create_expense()
        expense.company_id.vat = fromstring(
            self.xml_signed).Receptor.get('Rfc')
        self.create_attachment(expense.id)
        sheet = expense.sheet_id.with_context(
            expense.submit_expenses()['context']).create({})
        sheet.approve_expense_sheets()
        invoice = self.invoice_obj.search([('expense_id', '=', expense.id)])
        self.assertTrue(invoice, sheet.message_ids.mapped('body'))
        # Try attach again the same attachment
        expense = self.create_expense()
        self.create_attachment(expense.id)
        sheet = expense.sheet_id.with_context(
            expense.submit_expenses()['context']).create({})
        sheet.approve_expense_sheets()
        message = sheet.message_ids.mapped('body')
        self.assertTrue('The XML UUID belongs to other invoice' in ''.join(
            message), message)

    def test_expense_own_account(self):
        # Expense to employee
        expense = self.create_expense()
        expense.company_id.vat = fromstring(
            self.xml_signed).Receptor.get('Rfc')
        expense.payment_mode = 'own_account'
        self.create_attachment(expense.id)
        sheet = expense.sheet_id.with_context(
            expense.submit_expenses()['context']).create({})
        sheet.approve_expense_sheets()
        invoice = self.invoice_obj.search([('expense_id', '=', expense.id)])
        self.assertEquals(
            invoice.state, 'paid', sheet.message_ids.mapped('body'))

    def create_expense(self):
        return self.env['hr.expense'].create({
            'name': 'Expense demo',
            'product_id': self.product.id,
            'unit_amount': 100.0,
            'quantity': 1,
            'employee_id': self.employee.id,
            'payment_mode': 'company_account',
        })

    def create_attachment(self, expense_id):
        return self.env['ir.attachment'].create({
            'name': 'expense.xml',
            'datas': base64.encodestring(self.xml_signed),
            'datas_fname': 'expense.xml',
            'description': 'XML signed.',
            'res_model': 'hr.expense',
            'res_id': expense_id,
        })
