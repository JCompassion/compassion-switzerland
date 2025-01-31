##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    @author: Jonathan Guerne <guernej@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, _
from odoo.tools import html_escape as escape


class TextAreaWidget(models.AbstractModel):
    _name = "website_compassion.form.widget.textarea"
    _inherit = "cms.form.widget.mixin"
    _w_template = "website_compassion.field_widget_textarea"


class ContactUsForm(models.AbstractModel):
    """
    Form to create a new claim
    """

    _name = "cms.form.claim.contact.us"
    _inherit = "cms.form"

    _form_model = "crm.claim"
    _form_model_fields = ["partner_id", "name", "subject"]
    _form_required_fields = ["name", "subject"]
    form_buttons_template = "cms_form_compassion.modal_form_buttons"

    partner_id = fields.Many2one("res.partner", readonly=False)

    name = fields.Char("Question / Comment")
    subject = fields.Char("Request subject")

    def form_title(self):
        return _("Contact Us")

    def form_description(self):
        return _("If you have any questions, do not hesitate to contact us using the form below, "
                 "we will answer you as soon as possible.")

    @property
    def submit_text(self):
        return _("Send message")

    @property
    def form_msg_success_created(self):
        return _(
            "Thank you for your message and for your interest in the development of children in need. "
            "We will contact you as soon as possible."
        )

    @property
    def _form_fieldsets(self):
        fields = [
            {"id": "subject",
             "fields": ["subject", "partner_id"]},
            {"id": "question",
             "fields": ["name"]},
        ]

        return fields

    @property
    def form_widgets(self):
        # Hide fields
        res = super(ContactUsForm, self).form_widgets
        res.update(
            {
                "partner_id": "cms_form_compassion.form.widget.hidden",
                "name": "website_compassion.form.widget.textarea",
            }
        )
        return res

    def form_before_create_or_update(self, values, extra_values):

        # Find the corresponding claim category
        subject = values.get("subject")
        category_ids = self.env["crm.claim.category"].sudo().search(
            [("keywords", "!=", False)]
        )
        category_id = False
        for record in category_ids:
            if any(word in subject for word in record.get_keys()):
                category_id = record.id
                break

        super().form_before_create_or_update(values, extra_values)
        values.update({
            "partner_id": self.partner_id.id,
            "categ_id": category_id,
            "user_id": False,
            "language": self.main_object.detect_lang(values.get("name")).lang_id.code,
            "email_from": self.partner_id.email,
            "stage_id": self.sudo().env.ref("crm_claim.stage_claim1").id,
        })

    def form_after_create_or_update(self, values, extra_values):
        super().form_after_create_or_update(values, extra_values)

        subject = values.get("subject")
        body = values.get("name")
        partner = self.partner_id

        self.main_object.message_post(
            body=body,
            subject=_("Original request from %s %s ") % (partner.firstname, partner.lastname),
        )

        self.env["mail.mail"].sudo().create(
            {
                "state": "sent",
                "subject": subject,
                "body_html": body,
                "author_id": partner.id,
                "email_from": partner.email,
                "mail_message_id": self.env["mail.message"].sudo().create(
                    {
                        "model": "res.partner",
                        "res_id": partner.id,
                        "body": escape(body),
                        "subject": subject,
                        "author_id": partner.id,
                        "subtype_id": self.env.ref("mail.mt_comment").id,
                        "date": fields.Datetime.now(),
                    }
                ).id,
            })

    def _form_create(self, values):
        self.main_object = self.form_model.sudo().create(values.copy())

    def form_init(self, request, main_object=None, **kw):
        form = super().form_init(request, main_object=main_object, **kw)
        form.partner_id = kw.get("partner_id")
        return form
