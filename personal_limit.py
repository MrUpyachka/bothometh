from datetime import datetime, timedelta

from telebot.types import Message, Chat

from logger import LOG
from message_utils import get_message_author_username


def calculate_minutes_diff(last, past):
    return (last - past) // timedelta(minutes=1)


class CommandStats:
    def __init__(self, usage_limit=3):
        self.used_count = 0
        self.usage_limit = usage_limit
        self.first_abuse_date_time = None


class PersonalUsageLimit:
    def __init__(self, chats_history_limit=30, limit_reset_interval_minutes=60 * 3):
        self.chats_history_limit = chats_history_limit
        self.limit_reset_interval_minutes = limit_reset_interval_minutes
        self.chats_stats = {}

    def update_stats(self, message: Message, command):
        if self.check_history_limit_exceeded(message):
            LOG.warning('Personal limit tracker exceeded number of chats.')
            return
        stats = self.get_command_stats(message.chat, get_message_author_username(message), command)
        if stats:
            stats.used_count += 1

    def check_history_limit_exceeded(self, message):
        return message.chat.id not in self.chats_stats and len(self.chats_stats) >= self.chats_history_limit

    def check_available(self, message: Message, command):
        chat = message.chat
        if self.check_history_limit_exceeded(message):
            LOG.warning('Personal limit tracker exceeded number of chats. No tracking for chat %s (%s)',
                        chat.id, chat.title)
            return True
        author_username = get_message_author_username(message)
        stats = self.get_command_stats(message.chat, author_username, command)
        if not stats:
            LOG.debug('No statistic available for chat %s (%s). Commands allowed by default.', chat.id, chat.title)
            return True
        if stats.used_count >= stats.usage_limit:
            if not stats.first_abuse_date_time:
                LOG.debug('Command limit exceeded for user %s and command %s.', author_username, command)
                stats.first_abuse_date_time = datetime.now()
            elif calculate_minutes_diff(datetime.now(),
                                        stats.first_abuse_date_time) > self.limit_reset_interval_minutes:
                LOG.debug('It\'s time to refresh limit for user %s and command %s.', author_username, command)
                stats.first_abuse_date_time = None
                stats.used_count = 0
                return True
            LOG.debug('No usage attempts available for user %s and command %s.', author_username, command)
            return False
        return True

    def get_command_stats(self, chat: Chat, username, command):
        user_stats = self.get_user_stats(chat, username)
        if command not in user_stats:
            command_stats = CommandStats()
            user_stats[command] = command_stats
            return command_stats
        return user_stats[command]

    def get_user_stats(self, chat: Chat, username):
        chat_stats = self.get_chat_stats(chat)
        if username not in chat_stats:
            user_stats = {}
            chat_stats[username] = user_stats
            return user_stats
        return chat_stats[username]

    def get_chat_stats(self, chat: Chat):
        chat_id = chat.id
        if chat_id not in self.chats_stats:
            stats = {}
            self.chats_stats[chat_id] = stats
            return stats
        return self.chats_stats[chat_id]
