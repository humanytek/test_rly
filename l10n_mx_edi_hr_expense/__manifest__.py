# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo Mexico Localization for Expenses',
    'version': '10.0.1.0.0',
    'author': 'Vauxoo',
    'category': 'Accounting',
    'license': 'OEEL-1',
    'depends': [
        'hr_expense',
        'l10n_mx_edi_vendor_bills',
    ],
    'data': [
        "views/hr_employee_views.xml",
        "views/hr_expense_views.xml",
    ],
    'installable': True,
}
