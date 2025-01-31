##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Philippe Heer <heerphilippe@msn.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models


class ChildLifecycle(models.Model):
    """ Send Communication when Child Lifecycle Event is received. """

    _inherit = "compassion.child.ble"

    @api.model
    def process_commkit(self, commkit_data):
        ids = super().process_commkit(commkit_data)
        for lifecycle in self.browse(ids).filtered("child_id.sponsor_id"):
            # Planned Exit notification
            if lifecycle.type == "Planned Exit":
                communication_type = self.env.ref(
                    "partner_communication_switzerland.planned_exit_notification"
                )
                sponsorship = lifecycle.child_id.sponsorship_ids[:1]
                comm = sponsorship.send_communication(communication_type, both=True)
                # TODO remove this when all languages are set (comm will be set to
                #  auto_send)
                if sponsorship.correspondent_id.lang in ("fr_CH", "de_DE"):
                    comm.send()
            else:
                communication_type = self.env["partner.communication.config"].search(
                    [
                        ("name", "ilike", lifecycle.type),
                        ("name", "like", "Beneficiary"),
                        ("name", "not like", "Exit")  # Departures are treated
                        # when sub is created.
                    ]
                )
                if communication_type:
                    self.env["partner.communication.job"].create(
                        {
                            "config_id": communication_type.id,
                            "partner_id": lifecycle.child_id.sponsor_id.id,
                            "object_ids": lifecycle.child_id.id,
                            "user_id": communication_type.user_id.id,
                        }
                    )
        return ids


class ProjectLifecycle(models.Model):
    """ Send Communication when fcp lifecycle is received. """

    _inherit = "compassion.project.ile"

    @api.model
    def process_commkit(self, commkit_data):
        ids = super().process_commkit(commkit_data)

        for lifecycle in self.browse(ids):
            search = [
                ("name", "ilike", lifecycle.type),
                ("name", "like", "Project"),
            ]

            if lifecycle.type == "Suspension":
                if not lifecycle.hold_cdsp_funds:
                    # Avoid sending communication if funds are not held
                    continue
                if lifecycle.extension_2:
                    search.append(("name", "ilike", "Extension 2"))
                elif lifecycle.extension_1:
                    search.append(("name", "ilike", "Extension 1"))
                else:
                    search.append(("name", "=", "Project Suspension"))
            communication_type = self.env["partner.communication.config"].search(search)
            if communication_type and len(communication_type) == 1:
                for child in self.env["compassion.child"].search(
                        [
                            ("project_id", "=", lifecycle.project_id.id),
                            ("sponsor_id", "!=", False),
                        ]
                ):
                    self.env["partner.communication.job"].create(
                        {
                            "config_id": communication_type.id,
                            "partner_id": child.sponsor_id.id,
                            "object_ids": child.id,
                            "user_id": communication_type.user_id.id,
                        }
                    )
        return ids
