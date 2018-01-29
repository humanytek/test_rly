# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Mexican Vendor Bills",
    "version": "10.0.0.0.0",
    "author": "Vauxoo",
    "category": "Accounting",
    "website": "http://www.vauxoo.com",
    "license": "OEEL-1",
    "depends": [
        "account",
        "document",
    ],
    "demo": [
    ],
    "data": [
        "wizards/attach_fiscal_documents_view.xml",
        "views/assets.xml",
        "views/invoice_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    'images': [
        'images/main_screenshot.png'
    ],
    "qweb": [
        'static/src/xml/*.xml',
    ],
}
