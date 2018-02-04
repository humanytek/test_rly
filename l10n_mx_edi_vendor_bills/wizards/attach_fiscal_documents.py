# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from __future__ import division
import base64
from codecs import BOM_UTF8
from odoo.tools.float_utils import float_is_zero
from odoo import api, fields, models, _
from lxml import objectify, etree


class AttachXmlsWizard(models.TransientModel):
    _name = 'l10n_mx_base.attachment.wizard'

    dragndrop = fields.Char(help='Field to upload files')

    @api.multi
    def collect_taxes(self, taxes_xml):
        """ Get tax data of the Impuesto node of the xml and return
        dictionary with taxes datas
            Args:
                taxes_xml: Impuesto node of xml
        """
        taxes = []
        tax_codes = {'001': 'ISR', '002': 'IVA', '003': 'IEPS'}
        for rec in taxes_xml:
            tax_xml = rec.get('impuesto', rec.get('Impuesto', ''))
            tax_xml = tax_codes.get(tax_xml, tax_xml)
            amount_xml = float(rec.get('importe', rec.get('Importe', '0.0')))
            rate_xml = float(
                rec.get('tasa', float(rec.get('TasaOCuota', '0.0')) * 100))
            if 'Retenciones' in rec.getparent().tag:
                tax_xml = tax_xml + '-RET'
                amount_xml = amount_xml * -1
                rate_xml = rate_xml * -1

            taxes.append({'rate': rate_xml, 'tax': tax_xml,
                          'amount': amount_xml})
        return taxes

    @api.multi
    def create_invoice(self, xml, supplier, currency_id, taxes):
        """ Create supplier invoice from xml file
            Args:
                xml : xml file with the datas of purchase
                supplier: (res.partner) supplier partner
                currency_id: (res.currency) payment currency of the purchase
                taxes: list with the datas of taxes
        """
        inv_obj = self.env['account.invoice']
        line_obj = self.env['account.invoice.line']
        journal = inv_obj.with_context(type='in_invoice')._default_journal()
        prod_obj = self.env['product.product']
        # sat_code_obj = self.env['l10n_mx_edi.product.sat.code']
        uom_obj = uom_obj = self.env['product.uom']
        default_account = line_obj.with_context({
            'journal_id': journal.id, 'type': 'in_invoice'})._default_account()
        invoice_line_ids = []
        msg = (_('Some products are not found in the system, and the account '
                 'that is used like default is not configured in the journal, '
                 'please set default account in the journal '
                 '%s to create the invoice.') % journal.name)

        try:
            date_inv = xml.get('Fecha', '').split('T')
            uuid = inv_obj.l10n_mx_edi_get_tfd_etree(xml).get('UUID', '')
            for rec in xml.Conceptos.Concepto:
                name = rec.get('Descripcion', '')
                no_id = rec.get('NoIdentificacion', name)
                uom = rec.get('Unidad', '')
                # uom_code = rec.get('ClaveUnidad', '')
                qty = rec.get('Cantidad', '')
                price = rec.get('ValorUnitario', '')
                amount = rec.get('Importe', '0.0')
                product_id = prod_obj.search([
                    '|', ('default_code', '=ilike', no_id),
                    ('name', '=ilike', name)], limit=1)
                account_id = (
                    product_id.property_account_expense_id.id or product_id.
                    categ_id.property_account_expense_categ_id.id or
                    default_account)

                if not account_id:
                    return {
                        'key': False, 'where': 'CreateInvoice',
                        'error': [
                            _('Account to set in the lines not found.<br/>'),
                            msg]}

                if amount:
                    discount = (float(xml.get('Descuento', '0.0')) / float(
                        amount)) * 100

                domain_uom = [('name', '=ilike', uom)]
                line_taxes = []
                # line_taxes = [tax.get('id') for tax in
                #                 self.get_impuestos(rec).get('taxes_ids', [])]
                # code_sat = sat_code_obj.search(
                #     [('code', '=', uom_code)], limit=1)
                # domain_uom = [
                #     ('l10n_mx_edi_code_sat_id', '=', code_sat.id)]

                uom_id = uom_obj.with_context(
                    lang='es_MX').search(domain_uom, limit=1)

                invoice_line_ids.append((0, 0, {
                    'product_id': product_id.id,
                    'account_id': account_id,
                    'name': name,
                    'quantity': float(qty),
                    'uom_id': uom_id.id,
                    'invoice_line_tax_ids': [(6, 0, line_taxes)],
                    'price_unit': float(price),
                    'discount': discount,
                }))

            xml_str = etree.tostring(xml, pretty_print=True, encoding='UTF-8')
            invoice_id = inv_obj.create({
                'partner_id': supplier.id,
                'reference': xml.get('folio', xml.get('Folio', '')),
                'date_invoice': date_inv[0],
                'currency_id': (
                    currency_id.id or self.env.user.company_id.currency_id.id),
                'invoice_line_ids': invoice_line_ids,
                'type': 'in_invoice',
                'l10n_mx_edi_uuid': uuid,
                'xml_signed': xml_str,
                'l10n_mx_edi_time_invoice': date_inv[1],
                'journal_id': journal.id,
                'cfdi_complemento': 'na',
            })

            invoice_id._compute_l10n_mx_report_name()
            invoice_id.generate_xml_attachment(xml_str)

            return {'key': True, 'invoice_id': invoice_id.id}
        except BaseException as exce:
            return {
                'key': False, 'where': 'CreateInvoice',
                'error': [exce.__class__.__name__, str(exce)]}

    def get_impuestos(self, xml):

        if not hasattr(xml, 'Impuestos'):
            return {}

        taxes_list = {'wrong_taxes': [], 'taxes_ids': []}
        taxes_xml = xml.Impuestos
        taxes = []

        if hasattr(taxes_xml, 'Traslados'):
            taxes = self.collect_taxes(taxes_xml.Traslados.Traslado)
        if hasattr(taxes_xml, 'Retenciones'):
            taxes += self.collect_taxes(taxes_xml.Retenciones.Retencion)

        for tax in taxes:
            tax_group_id = self.env['account.tax.group'].search(
                [('name', '=', tax['tax'])], limit=1)
            domain = [('tax_group_id', 'in', tax_group_id.ids),
                      ('type_tax_use', '=', 'purchase')]

            name = ''
            if 'RET' not in tax['tax'] or tax['rate']:
                domain += [('amount', '=', tax['rate'])]
                name = '%s(%s%%)' % (tax['tax'], tax['rate'])

            tax_get = self.env['account.tax'].search(domain, limit=1)

            if not tax_group_id or not tax_get:
                taxes_list['wrong_taxes'].append(
                    '%s(%s%%)' % (tax['tax'], tax['rate']))
            else:
                tax['id'] = tax_get.id
                tax['account'] = tax_get.account_id.id
                tax['name'] = name if name else tax['tax']
                taxes_list['taxes_ids'].append(tax)
        return taxes_list

    @api.model
    def check_xml(self, xml64, key):
        """Validate that attributes in the XML before create invoice
        or attach.
        :param str xml64: The CFDI in base64
        :param str key: Is the document name
        :return: A dictionary with the next attributes
            - key.- If all is OK return True, else False
            - xml64.- The same CFDI in base64
            - where.- The process that was executed
            - error.- If is found, return the message
            - invoice_id.- The invoice realated
        :rtype: dict
        """
        inv_id = self.env.context.get('active_id', [])
        inv_obj = self.env['account.invoice']
        inv = inv_obj.browse(inv_id)
        try:
            xml_str = base64.decodestring(xml64.replace(
                'data:text/xml;base64,', '')).lstrip(BOM_UTF8)
            xml = objectify.fromstring(xml_str)
            xml_vat_emitter = xml.Emisor.get('Rfc', '').upper()
            xml_vat_receiver = xml.Receptor.get('Rfc', '').upper()
            xml_amount = xml.get('Total', 0.0)
            xml_uuid = inv.l10n_mx_edi_get_tfd_etree(xml).get('UUID', '')
            xml_folio = xml.get('Folio', '')
            xml_currency = xml.get('Moneda', 'MXN')
            xml_taxes = self.get_impuestos(xml)
            xml_discount = float(xml.get('Descuento', '0.0'))
            xml_name_supplier = xml.Emisor.get('Nombre', '')
        except (AttributeError, SyntaxError) as exce:
            return {key: False, 'xml64': xml64, 'where': 'CheckXML',
                    'error': [exce.__class__.__name__, str(exce)]}

        validate_xml = inv._validate_xml_sat(
            xml_vat_emitter, xml_vat_receiver, xml_amount, xml_uuid)
        inv_vat_receiver = (
            self.env.user.company_id.vat or '').upper()
        inv_vat_emitter = (inv.commercial_partner_id.vat or '').upper()
        inv_amount = inv.amount_total or 0.0
        inv_folio = inv.reference or ''
        exist_supplier = self.env['res.partner'].search(
            ['&', ('vat', '=', 'MX%s' % (xml_vat_emitter)), '|',
             ('supplier', '=', True), ('customer', '=', True)], limit=1)
        exist_reference = xml_folio and inv_obj.search(
            [('reference', '=', xml_folio),
             ('partner_id', '=', exist_supplier.id)], limit=1)
        uuid_dupli = inv.search([
            ('l10n_mx_edi_uuid', '=', xml_uuid), ('id', '!=', inv.id)],
            limit=1)
        mxns = ['mxp', 'mxn', 'pesos', 'peso mexicano', 'pesos mexicanos']
        xml_currency = 'MXN' if xml_currency.lower() in mxns else xml_currency

        exist_currency = self.env['res.currency'].search(
            [('name', '=', xml_currency)], limit=1)
        error = [
            (not xml_uuid, {'signed': True}),
            (validate_xml.Estado == 'Cancelado', {'cancel': True}),
            ((xml_uuid and uuid_dupli), {'uuid_duplicate': (
                uuid_dupli.partner_id.name, uuid_dupli.reference)}),
            ((inv_vat_receiver != 'MX%s' % (xml_vat_receiver)),
             {'rfc': (xml_vat_receiver, inv_vat_receiver)}),
            ((not inv_id and exist_reference),
             {'reference': (xml_name_supplier, xml_folio)}),
            ((not inv_id and xml_discount), {'discount': True}),
            ((not inv_id and not exist_supplier),
             {'supplier': xml_name_supplier}),
            ((not inv_id and xml_currency and not exist_currency),
             {'currency': xml_currency}),
            ((not inv_id and xml_taxes.get('wrong_taxes', False)),
             {'taxes': xml_taxes.get('wrong_taxes', False)}),
            ((inv_id and inv_folio != xml_folio),
             {'folio': (xml_folio, inv_folio)}),
            ((inv_id and inv_vat_emitter != 'MX%s' % (xml_vat_emitter)), {
                'rfc_supplier': (xml_vat_emitter, inv_vat_emitter)}),
            ((inv_id and not float_is_zero(float(inv_amount) - float(
                xml_amount), precision_digits=2)), {
                    'amount': (xml_amount, inv_amount)})
        ]
        msg = {}
        for e in error:
            if e[0]:
                msg.update(e[1])
        if msg:
            msg.update({key: False, 'xml64': xml64})
            return msg

        if not inv_id:
            invoice_status = self.create_invoice(
                xml, exist_supplier, exist_currency,
                xml_taxes.get('taxes_ids', []))
            if invoice_status['key']:
                del invoice_status['key']
                invoice_status.update({key: True})
                return invoice_status

            del invoice_status['key']
            invoice_status.update({key: False, 'xml64': xml64})
            return invoice_status

        inv.write({'l10n_mx_edi_uuid': xml_uuid})
        inv._compute_l10n_mx_report_name()
        inv.generate_xml_attachment(xml_str)
        return {key: True, 'invoice_id': inv.id}

    @api.model
    def create_partner(self, xml64, key):
        """ It creates the supplier dictionary, getting data from the XML
        Receives an xml decode to read and returns a dictionary with data """
        try:
            xml = objectify.fromstring(base64.decodestring(xml64.replace(
                'data:text/xml;base64,', '')).lstrip(BOM_UTF8))

            # Default Mexico because only in Mexico are emitted CFDIs
            country_id = self.env.ref('base.mx')
            reference_xml = xml.get('Folio', '')

            rfc_emitter = xml.Emisor.get('Rfc', False)
            name_emitter = xml.Emisor.get('Nombre', rfc_emitter)

            partner = self.env['res.partner'].create({
                'name': name_emitter,
                'company_type': 'company',
                'vat': rfc_emitter,
                'ref': rfc_emitter,
                'country_id': country_id.id,
                'supplier': True,
                'customer': False,
            })
            msg = _('This partner was created when invoice %s was added from '
                    'a XML file. Please verify that the datas of partner are '
                    'correct.') % reference_xml
            partner.message_post(subject=_('Info'), body=msg)
            return self.check_xml(xml64, key)
        except BaseException as exce:
            return {
                key: False, 'xml64': xml64, 'where': 'CreatePartner',
                'error': [exce.__class__.__name__, str(exce)]}
