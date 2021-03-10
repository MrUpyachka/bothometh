from telebot import TeleBot

import message_utils
import replies_settings
from logger import LOG
from replies_history import RepliesHistory
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def is_sticker(reply):
    return reply['contentType'] == 'sticker'


def extract_reply_desc(reply):
    return reply['description']


class Replier:
    def __init__(self, bot: TeleBot, replies_history: RepliesHistory):
        self.replies_history = replies_history
        self.bot = bot

    def resolve_send_function(self, reply):
        if is_sticker(reply):
            return self.bot.send_sticker
        return self.bot.send_message

    def reply_randomly(self, chat, replies_set_ref, message_to_reply=None):
        target_message_id = message_to_reply.id if message_to_reply else None
        reply = self.replies_history.select_not_recently_used(replies_set_ref)
        if not reply:
            LOG.info("Unable to select reply for '%s'", replies_set_ref)
            return
        content = replies_settings.extract_reply_content(reply)
        self.resolve_send_function(reply)(chat.id, content, reply_to_message_id=target_message_id)
        self.replies_history.update_recently_used_replies(replies_set_ref, reply)
        LOG.info("Replied to %s with '%s' from '%s'",
                 message_utils.get_message_author_username(message_to_reply) if message_to_reply else chat.title,
                 extract_reply_desc(reply),
                 replies_set_ref)
