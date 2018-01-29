# -*- coding: utf-8 -*-
# Copyright 2018 Vauxoo (Oscar Alcala <oscar@vauxoo.com>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import json
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError
from odoo.addons.website_portal.controllers.main import website_account


class SaleOrderAttachments(http.Controller):

    @http.route(
        ['/purchase/order_attachments/<int:order_id>'],
        type='http', auth="user", methods=['POST'], website=True)
    def attach_files(self, order_id, **post):
        purchase_obj = request.env['purchase.order']
        att_obj = request.env['ir.attachment']
        xml = post.get('xml[0]')
        errors, filename = att_obj.parse_xml(xml)
        if not errors.get(xml.filename):
            return json.dumps({'error_messages': errors})
        att_ids = purchase_obj.insert_attachment(
            'purchase.order', order_id, post, filename)
        return json.dumps({'id': att_ids._ids})


class WebsiteAccount(website_account):

    @http.route()
    def account(self, **kw):
        """ Add purchase documents to main account page """
        response = super(WebsiteAccount, self).account(**kw)
        partner = request.env.user.partner_id

        purchase_obj = request.env['purchase.order'].sudo()
        response.qcontext['purchases'] = purchase_obj.search([
            '|',
            ('message_partner_ids',
             'child_of', [partner.commercial_partner_id.id]),
            ('partner_id', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['purchase', 'done', 'cancel'])
        ])
        return response

    @http.route(
        ['/my/purchase', '/my/purchase/page/<int:page>'],
        type='http',
        auth="user",
        website=True)
    def portal_my_purchase_orders(
            self, page=1, date_begin=None, date_end=None, sortby=None,
            filterby=None, **kw):
        """ Shows list of purchase orders """
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        po = request.env['purchase.order']
        domain = [
            '|',
            ('message_partner_ids',
             'child_of', [partner.commercial_partner_id.id]),
            ('partner_id', 'child_of', [partner.commercial_partner_id.id]),
        ]
        archive_groups = self._get_archive_groups(
            'purchase.order', domain,
            fields=['name', 'date_order'],
            groupby='date_order',
            order='date_order desc')
        if date_begin and date_end:
            domain += [('date_order', '>', date_begin),
                       ('date_order', '<=', date_end)]
        searchbar_sortings = {
            'date': {
                'label': _('Newest'),
                'order': 'date_order desc, id desc'
            },
            'name': {
                'label': _('Name'),
                'order': 'name asc, id asc'
            },
            'amount_total': {
                'label': _('Total'),
                'order': 'amount_total desc, id desc'
            },
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # default filter by value
        if not filterby:
            filterby = 'all'
        # count for pager
        purchase_count = po.search_count(domain)
        # make pager
        pager = request.website.pager(
            url="/my/purchase",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=purchase_count,
            page=page,
            step=self._items_per_page
        )
        # search the purchase orders to display, according to the pager data
        orders = po.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_purchases_history'] = orders.ids[:100]
        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'purchase',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'filterby': filterby,
            'default_url': '/my/purchase',
        })
        return request.render(
            "l10n_mx_portal_vendor_bills.portal_my_purchase_orders", values)

    @http.route(
        ['/my/purchase/<int:order_id>'],
        type='http',
        auth="user",
        website=True)
    def portal_my_purchase_order(self, order_id=None, **kw):
        order = request.env['purchase.order'].browse(order_id)
        try:
            order.check_access_rights('read')
            order.check_access_rule('read')
        except AccessError:
            return request.redirect('/my')
        values = {
            'order': order.sudo(),
        }
        return request.render(
            "l10n_mx_portal_vendor_bills.portal_my_purchase_order", values)
