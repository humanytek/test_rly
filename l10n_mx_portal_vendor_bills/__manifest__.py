# -*- coding: utf-8 -*-
# Copyright 2018 Vauxoo (Oscar Alcala <oscar@vauxoo.com>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Portal for purchase documents",
    "summary": """
        Allows suppliers to upload documents related to Purchase Orders
        such as:

        - Invoice's XML file
        - Invoice's PDF file
        - Purchase order
        - Acknowledgment of receipt
    """,
    "version": "10.0.1.0.0",
    "author": "Vauxoo",
    "category": "Localization/Mexico",
    "website": "http://www.vauxoo.com/",
    "license": "LGPL-3",
    "depends": [
        'l10n_mx_edi_vendor_bills',
        'purchase',
        'website_portal',
    ],
    "demo": [
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/portal_templates.xml',
        'views/partner_view.xml',
    ],
    "installable": True,
    "auto_install": False,
}
