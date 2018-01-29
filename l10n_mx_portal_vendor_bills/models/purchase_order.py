# -*- coding: utf-8 -*-
# Copyright 2018 Vauxoo (Oscar Alcala <oscar@vauxoo.com>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
from odoo import models, api, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def insert_attachment(self, model, id_record, files, filename):
        record = self.env[model].browse(id_record)
        attachment_obj = self.env['ir.attachment'].sudo()
        # if asuffix is required add to this dict the input name and
        # the suffix to add to the file name
        suffixes = {
            'purchase_order[0]': 'PO',
            'receipt[0]': 'AC'
        }
        for fname, xml_file in files.items():
            suffix = suffixes.get(fname, '')
            new_name = filename if not suffix else '%s_%s' % (filename, suffix)
            attachment_value = {
                'name': '%s.%s' % (new_name, xml_file.mimetype.split('/')[1]),
                'datas': base64.encodestring(xml_file.read()),
                'datas_fname': xml_file.filename,
                'res_model': model,
                'res_id': record.id,
            }
            attachment_obj += attachment_obj.create(attachment_value)
        return attachment_obj


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_indirect = fields.Boolean('Indirect Supplier')
