# -*- coding: utf-8 -*-
# Copyright 2018 Vauxoo (Oscar Alcala <oscar@vauxoo.com>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import base64
from codecs import BOM_UTF8
from lxml import objectify
from odoo import models, api

BOM_UTF8U = BOM_UTF8.decode('UTF-8')


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @staticmethod
    def get_etree(cfdi):
        """Get the node from the namespace specified from the
        XML file.
        :param xml object cfdi: The cfdi as etree
        :return: the specified on the namespace
        :rtype: lxml.objectify
        """
        # Verify if it's signed
        if not hasattr(cfdi, 'Complemento'):
            return {}
        attribute = '//cfdi:Emisor'
        namespace = {'cfdi': 'http://www.sat.gob.mx/cfd/3'}
        node = cfdi.xpath(attribute, namespaces=namespace)
        return node[0] if node else {}

    @api.model
    def parse_xml(self, xml_file):
        """Simple wrapper to the wizard that runs the whole process of the
        importation of documents on the backend, some extra steps are done
        here:
        - Creation of custom filename: rfc-emisor_folio_serie_AnoMesDia
        - Validate if the CFDI is v 3.3

        :param xml_file: The filestorage itself.
        :return filename: The new filename which will be used to store the
        attachment.
        :rtype string:
        :return: A dictionary with the following attributes
            - key.- If all is OK return True, else False
            - xml64.- The same CFDI in base64
            - where.- The file on which the process was executed
            - error.- If it's found, return the message
            - invoice_id.- The newly created invoice
        :rtype dict:
        """

        # Instancing the wizard that will import the xml file
        wiz = self.env['l10n_mx_base.attachment.wizard'].sudo()
        data = base64.encodestring(xml_file.read())
        res = wiz.check_xml(data, xml_file.filename)
        xml_string = base64.decodestring(data).lstrip(BOM_UTF8)
        xml = objectify.fromstring(xml_string)
        parsed_node = self.get_etree(xml)

        cfdi_version = parsed_node.getparent().get('Version', False)
        if cfdi_version != '3.3':
            res['cfdi_version'] = True

        # early return if errors found
        if not res.get(xml_file.filename, True):
            return res, xml_file.filename

        # Extract data from xml file
        doc_number = parsed_node.getparent().get('Folio', False)
        serial = parsed_node.getparent().get('Serie', False)
        date = parsed_node.getparent().get('Fecha', False)
        supplier_vat = parsed_node.get('Rfc', False)

        # create base filename
        filename = '%s_%s_%s_%s' % (
            supplier_vat, doc_number, serial, date[:10])

        return res, filename
