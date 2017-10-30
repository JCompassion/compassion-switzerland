# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import models, api


class MailThread(models.AbstractModel):
    """
    Only allow employees as followers
    """
    _inherit = 'mail.thread'

    @api.multi
    def message_subscribe(self, partner_ids=None, channel_ids=None,
                          subtype_ids=None, force=True):
        partners = self.env['res.partner'].browse(partner_ids)
        allowed = partners.mapped('user_ids').filtered(lambda u: not u.share)
        partner_ids = allowed.mapped('partner_id.id')
        return super(MailThread, self).message_subscribe(
            partner_ids, channel_ids, subtype_ids, force)

    @api.multi
    def _message_auto_subscribe_notify(self, partner_ids):
        partners = self.env['res.partner'].browse(partner_ids)
        allowed = partners.mapped('user_ids').filtered(lambda u: not u.share)
        partner_ids = allowed.mapped('partner_id.id')
        super(MailThread, self)._message_auto_subscribe_notify(partner_ids)

    @api.multi
    def message_get_suggested_recipients(self):
        result = super(MailThread, self).message_get_suggested_recipients()
        to_remove = list()
        partner_obj = self.env['res.partner']
        for message_id, suggestion in result.iteritems():
            if suggestion:
                partner = partner_obj.browse(suggestion[0])
                users = partner.mapped('user_ids').filtered(
                    lambda u: not u.share)
                if not users:
                    to_remove.append(message_id)
        for message_id in to_remove:
            del result[message_id]
        return result
