from telebot.types import Chat


def is_private(chat: Chat):
    return chat.type == 'private'
