from logger import LOG
from telebot import TeleBot
import chat_utils


class AdminPermissionsChecker:
    def __init__(self, bot: TeleBot, bot_details, admin_check_history_limit=100):
        self.admin_check_history_limit = admin_check_history_limit
        self.admin_check_history = {}
        self.bot = bot
        self.bot_details = bot_details

    def save_admin_check_result(self, chat_id, status):
        if len(self.admin_check_history) >= self.admin_check_history_limit:
            LOG.debug('Admin check cache size exceeded, cleanup forced')
            self.admin_check_history.clear()
        self.admin_check_history[chat_id] = status
        LOG.debug('Admin check cache updated: chat_id=%s, status=%s, cache_size=%d',
                  chat_id, status, len(self.admin_check_history))

    def is_administrator(self, chat):
        if chat_utils.is_private(chat):
            return False
        chat_id = chat.id
        if chat_id in self.admin_check_history:
            return self.admin_check_history[chat_id]
        chat_admins = self.bot.get_chat_administrators(chat_id)
        admins_usernames = map(lambda r: r.user.username, chat_admins)
        admin_check_status = self.bot_details.username in admins_usernames
        self.save_admin_check_result(chat_id, admin_check_status)
        return admin_check_status

