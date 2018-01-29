# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import cgi
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
try:
    from suds.client import Client
except ImportError as err:
    _logger.debug(err)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    l10n_mx_edi_uuid = fields.Char(
        'Fiscal Folio', copy=False, index=True,
        help='Folio in electronic invoice, returned by SAT.')
    l10n_mx_edi_cfdi_name = fields.Char(help="File Name for new Attachment",
                                        readonly=True)

    @api.model
    def _validate_xml_sat(self, vat_emitter, vat_receiver, amount, uuid):
        """Validate XML state in SAT system"""
        url = 'https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc?wsdl'  # noqa
        try:
            return Client(url).service.Consulta('"?re=%s&rr=%s&tt=%s&id=%s' % (
                cgi.escape(cgi.escape(vat_emitter or '')),
                cgi.escape(cgi.escape(vat_receiver or '')),
                amount or 0.0, uuid or ''))
        except Exception as e:  # pragma: no cover
            raise ValidationError(e)  # pragma: no cover

    @staticmethod
    def l10n_mx_edi_get_tfd_etree(cfdi):
        """Get the TimbreFiscalDigital node from the cfdi.
        :param objectify cfdi: The cfdi as etree
        :return: the TimbreFiscalDigital node
        :rtype: objectify
        """
        if not hasattr(cfdi, 'Complemento'):
            return {}
        attribute = 'tfd:TimbreFiscalDigital[1]'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else {}

    @api.multi
    def _compute_l10n_mx_report_name(self):
        """Compute the attachment name
        """
        for invoice in self:
            fname = "%s_%s" % (invoice.company_id.partner_id.vat or '',
                               invoice.move_name or '')
            count = self.env['ir.attachment'].search_count(
                [('name', 'like', fname),
                 ('res_model', '=', 'account.invoice'),
                 ('res_id', '=', invoice.id),
                 ('mimetype', '=', 'application/xml'),
                 ])
            if count > 0:
                fname += '_%s' % (count + 1)
            invoice.l10n_mx_edi_cfdi_name = fname.replace('/', '')

    @api.multi
    def generate_xml_attachment(self, cfdi):
        self.ensure_one()
        name = '%s.xml' % self.l10n_mx_edi_cfdi_name
        data_attach = {
            'name': name,
            'datas': base64.encodestring(cfdi),
            'datas_fname': name,
            'description': _('XML signed from Invoice %s.' % self.number),
            'res_model': self._name,
            'res_id': self.id,
        }
        return self.env['ir.attachment'].with_context({}).create(data_attach)
