import collections

import message_utils
from logger import LOG


class MessagesHistory:
    def __init__(self, messages_history_limit=100):
        self.messages_history_limit = messages_history_limit
        self.messages_history = collections.deque([], messages_history_limit)

    def save(self, message):
        author = message_utils.get_message_author_username(message)
        self.messages_history.append(message)
        LOG.debug('%d messages saved. Last author: %s', len(self.messages_history), author)

    def get_last_message_of(self, author, chat):
        history = reversed(self.messages_history)
        for message in history:
            if message_utils.get_message_author_username(message) == author and message.chat.id == chat.id:
                LOG.debug('Found a message from %s in history of chat %s (%s)', author, chat.id, chat.title)
                return message
        LOG.debug('No messages found in history from %s in chat %s (%s)', author, chat.id, chat.title)
        return None
