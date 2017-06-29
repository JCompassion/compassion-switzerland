# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import datetime

from odoo.addons.mysql_connector.models.mysql_connector \
    import MysqlConnector


class TranslateConnect(MysqlConnector):
    """ Contains all the utility methods needed to talk with the MySQL server
        used by translate platform, as well as all mappings
        from OpenERP fields to corresponding MySQL fields.
    """

    def __init__(self):
        super(TranslateConnect, self).__init__(
            'mysql_translate_host',
            'mysql_translate_user',
            'mysql_translate_pw',
            'mysql_translate_db')

        self.current_time = datetime.datetime.now()

    def upsert_text(self, correspondence, file_name,
                    src_lang_id, dst_lang_iso):
        """Push or update text (db table) on local translate platform
        """
        child = correspondence.child_id
        sponsor = correspondence.correspondant_id

        self.letter_name = file_name
        child_age = datetime.date.today().year - int(child.birthdate[:4])

        text_type_id = 2 if correspondence.direction ==\
            'Supporter To Beneficiary' else 1

        first_letter_id = correspondence.env.ref(
            'sbc_compassion.correspondence_type_new_sponsor').id
        final_letter_id = correspondence.env.ref(
            'sbc_compassion.correspondence_type_final').id
        # Not urgent, default
        priority = 1
        type_ids = correspondence.communication_type_ids.ids
        if first_letter_id in type_ids or final_letter_id in type_ids:
            priority = 4

        vals = {
            'src_lang_id': src_lang_id,
            'aim_lang_id': dst_lang_iso,
            'title': self.letter_name,
            'file': self.letter_name,
            'codega': sponsor.ref,
            'gender': sponsor.title.name,
            'name': sponsor.name,
            'firstname': sponsor.firstname,
            'code': child.local_id,
            'kid_name': child.name,
            'kid_firstname': child.firstname,
            'age': child_age,
            'kid_gender': child.gender,
            'createdat': self.current_time,
            'updatedat': self.current_time,
            'priority_id': priority,
            'text_type_id': text_type_id,
        }
        return self.upsert("text", vals)

    def upsert_translation(self, text_id, letter):
        """Push or update translation (db table) on local translate platform
        """

        vals = {
            'file': self.letter_name[0:-4] + '.rtf',
            'text_id': text_id,
            'createdat': self.current_time,
            'updatedat': self.current_time,
            'toDo_id': 0,
            'letter_odoo_id': letter.id,
        }
        return self.upsert("translation", vals)

    def upsert_translation_status(self, translation_id):
        """Push or update translation_status (db table) on local translate
        platform
        """
        to_translate = 1
        vals = {
            'translation_id': translation_id,
            'status_id': to_translate,
            'createdat': self.current_time,
            'updatedat': self.current_time,
        }
        return self.upsert("translation_status", vals)

    def get_lang_id(self, lang_compassion_id):
        """ Returns the language's id in MySQL that has  GP_Libel pointing
         to the iso_code given (returns -1 if not found). """
        res = self.selectOne(
            "SELECT id FROM language WHERE GP_Libel LIKE '{}'"
            .format(lang_compassion_id.code_iso))
        return res['id'] if res else -1

    def get_translated_letters(self):
        """ Returns a list for dictionaries with translation and filename
        (sponsorship_id is in the file name...) in MySQL translation_test
        database that has translation_status to 'Traduit" (id = 3) and
        toDo_id to 'Pret' (id = 3)
        (returns -1 if not found). """
        res = self.selectAll("""
            SELECT tr.id, tr.letter_odoo_id, tr.text, txt.id AS text_id,
            l.GP_libel AS target_lang, usr.number AS translator
            FROM translation_status trs
            INNER JOIN translation tr
            ON trs.translation_id = tr.id
            INNER JOIN user usr
            ON tr.user_id = usr.id
            INNER JOIN text txt
            ON tr.text_id = txt.id
            INNER JOIN language l
            ON txt.aim_lang_id = l.id
            WHERE tr.letter_odoo_id IS NOT NULL
            AND trs.status_id = 3
            AND tr.toDo_id = 3
        """)
        return res

    def update_translation_to_not_in_odoo(self, translation_id):
        """update translation to set toDo_id in state "Pas sur Odoo"
        """

        vals = {
            'id': translation_id,
            'toDo_id': 5,
            'updatedat': self.current_time,
        }
        return self.upsert("translation", vals)

    def update_translation_to_treated(self, translation_id):
        """update translation to set toDo_id in state "Traité"
        """

        vals = {
            'id': translation_id,
            'toDo_id': 4,
            'updatedat': self.current_time,
        }
        return self.upsert("translation", vals)

    def remove_letter(self, id):
        """ Delete a letter record with the text_id given """
        self.remove_from_text(id)

    def remove_from_text(self, id):
        """ Delete a text record for the text_id given """
        self.query("DELETE FROM text WHERE id={}"
                   .format(id))

    def remove_translation_with_odoo_id(self, id):
        self.query("DELETE text FROM text INNER JOIN translation ON text.id\
             = translation.text_id WHERE translation.letter_odoo_id = {}"
                   .format(id))
