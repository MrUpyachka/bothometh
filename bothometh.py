import collections
import json
import logging
import os.path
import random
import sys
from shutil import copy

import telebot
from telebot import util as bot_utils

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)

LOG = logging

args = sys.argv
key = sys.argv[1]
settings_dir = sys.argv[2]
bot = telebot.TeleBot(key, threaded=False)
bot_details = bot.get_me()
LOG.debug('Bot details retrieved: %s', bot_details)
mentioned_key = '@' + bot_details.username

settings_file_path = settings_dir + '/settings.json'
settings_file_encoding = 'utf-8'
if not os.path.isdir(settings_dir):
    os.makedirs(settings_dir)
if not os.path.isfile(settings_file_path):
    copy('default_settings.json', settings_file_path)
with open(settings_file_path, 'r', encoding=settings_file_encoding) as settings_file:
    settings = json.load(settings_file)
developer_usernames = settings['developerUsernames']

command_to_reply_map = settings['commandToReplies']
replies_settings = settings['replies']
configured_commands = command_to_reply_map.keys()

messages_history_limit = 100
messages_history = collections.deque([], messages_history_limit)

admin_check_history_limit = 100
admin_check_history = {}


def write_settings_to_file():
    with open(settings_file_path, 'w', encoding=settings_file_encoding) as outfile:
        json.dump(settings, outfile)
    LOG.info('Settings file updated.')


def select_random(choices):
    return random.choice(choices)


def extract_reply_content(reply):
    return reply['content']


def extract_reply_desc(reply):
    return reply['description']


def is_sticker(reply):
    return reply['contentType'] == 'sticker'


def get_json_with_entities(message):
    if not hasattr(message, 'json'):
        return None
    json_val = message.json
    if 'entities' not in json_val:
        return None
    return json_val


def is_direct_message(message):
    return message.chat.type == 'private'


def are_we_mentioned(message):
    """Checks that bot mentioned in specified message"""
    if is_direct_message(message):
        return True
    json_val = get_json_with_entities(message)
    if not json_val:
        return False
    entities = json_val['entities']
    for ent in entities:
        if ent['type'] == 'mention' and bot_details.username in json_val['text']:
            return True
    return False


def get_mentioned_username(message):
    json_val = get_json_with_entities(message)
    if not json_val:
        return None
    entities = json_val['entities']
    for ent in entities:
        if ent['type'] == 'mention':
            text = json_val['text']
            # offset increased to remove @ sign
            start_position = ent['offset'] + 1
            mention_length = ent['length']
            return text[start_position:start_position + mention_length]
    return None


def get_reply_to_message(message):
    """Returns ID of message specified message replies to"""
    if not hasattr(message, 'reply_to_message'):
        return None
    reply_to_message = message.reply_to_message
    if reply_to_message is None or not hasattr(reply_to_message, 'message_id'):
        return None
    return reply_to_message


def get_message_author_username(message):
    from_user = message.from_user
    if from_user is None or not hasattr(from_user, 'username'):
        return None
    return from_user.username


def is_replied_to_us(message):
    """Checks that message replies to our own message"""
    reply_to_message = get_reply_to_message(message)
    if reply_to_message is None:
        return False
    if get_message_author_username(reply_to_message) == bot_details.username:
        return True
    return False


def save_to_history(message):
    author = get_message_author_username(message)
    messages_history.append(message)
    LOG.debug('%d messages saved. Last author: %s', len(messages_history), author)


def save_admin_check_result(chat_id, status):
    if len(admin_check_history) >= admin_check_history_limit:
        LOG.debug('Admin check cache size exceeded, cleanup forced')
        admin_check_history.clear()
    admin_check_history[chat_id] = status
    LOG.debug('Admin check cache updated: chat_id=%s, status=%s, cache_size=%d',
              chat_id, status, len(admin_check_history))


def extract_username(administrator):
    return administrator.user.username


def is_administrator(chat):
    chat_id = chat.id
    if chat_id in admin_check_history:
        return admin_check_history[chat_id]
    chat_admins = bot.get_chat_administrators(chat_id)
    admins_usernames = map(extract_username, chat_admins)
    save_admin_check_result(chat_id, bot_details.username in admins_usernames)


def get_last_message_of(author, chat):
    history = reversed(messages_history)
    for message in history:
        if get_message_author_username(message) == author and message.chat.id == chat.id:
            LOG.debug('Found a message from %s in history of chat %s (%s)', author, chat.id, chat.title)
            return message
    LOG.debug('No messages found in history from %s in chat %s (%s)', author, chat.id, chat.title)
    return None


def resolve_send_function(reply):
    if is_sticker(reply):
        return bot.send_sticker
    return bot.send_message


def reply_randomly(chat, message_to_reply, replies_set_ref):
    target_message_id = message_to_reply.id if message_to_reply else None
    replies_set = replies_settings[replies_set_ref]
    if not replies_set:
        LOG.info("No replies available for %s", replies_set_ref)
        return
    reply = select_random(replies_set)
    content = extract_reply_content(reply)
    resolve_send_function(reply)(chat.id, content, reply_to_message_id=target_message_id)
    LOG.info("Replied to %s with '%s' from '%s'",
             get_message_author_username(message_to_reply) if message_to_reply else chat.title,
             extract_reply_desc(reply),
             replies_set_ref)


def strong_reply(original_message, message_to_reply):
    reply_randomly(original_message.chat, message_to_reply, 'strongReply')


def check_if_message_from_developer(message):
    return get_message_author_username(message) in developer_usernames


def handle_if_message_from_developer(message, handler):
    if check_if_message_from_developer(message):
        handler(message)
    else:
        bot.reply_to(message, 'You are not my master!')
        strong_reply(message, message)


def toggle_dev_mode(message):
    mode = not settings['devModeEnabled']
    settings['devModeEnabled'] = mode
    LOG.info('Dev mode switched by chat command: %s', 'enabled' if mode else 'disabled')
    if mode:
        bot.reply_to(message, 'Send a sticker - I will provide you its code.')


def toggle_reactions(message):
    mode = not settings['simpleReplyEnabled']
    settings['simpleReplyEnabled'] = mode
    settings['strongReplyEnabled'] = mode
    LOG.info('Reactions mode switched by chat command: %s', 'enabled' if mode else 'disabled')


def is_simple_reply_allowed():
    return settings['simpleReplyEnabled']


def is_strong_reply_allowed():
    return settings['strongReplyEnabled']


def is_dev_mode_enabled():
    return settings['devModeEnabled']


def reply_if_mentioned(message):
    replied_to_us = is_replied_to_us(message)
    mentioned = are_we_mentioned(message)
    LOG.debug('Handling: replied_to_us=%s, mentioned=%s', replied_to_us, mentioned)
    if not replied_to_us and not mentioned:
        LOG.debug('Message ignored: %s', message)
        return  # not our business
    if is_strong_reply_allowed() and mentioned:
        msg_to_reply = get_reply_to_message(message)
        strong_reply(message, msg_to_reply if msg_to_reply else message)
        return
    if is_simple_reply_allowed() and replied_to_us:
        reply_randomly(message.chat, message, 'simpleReply')


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "What's up? Check 'https://github.com/MrUpyachka/bothometh'")


@bot.message_handler(commands=['toggle_dev_mode'])
def toggle_dev_mode_on_command(message):
    handle_if_message_from_developer(message, toggle_dev_mode)


@bot.message_handler(commands=['toggle_reactions'])
def toggle_reactions_on_command(message):
    handle_if_message_from_developer(message, toggle_reactions)


@bot.message_handler(commands=['save'])
def trigger_settings_save(message):
    handle_if_message_from_developer(message, lambda m: write_settings_to_file())


def mention_user(chat, username):
    return bot.send_message(chat.id, '@' + username)


def resolve_command_target_message(message):
    msg_to_reply = get_reply_to_message(message)
    if msg_to_reply:
        return msg_to_reply
    target_user = get_mentioned_username(message)
    if target_user:
        target_user_message = get_last_message_of(target_user, message.chat)
        if not target_user_message:
            mention_user(message.chat, target_user)
            return None
        return target_user_message
    return message


def handle_user_command(command, message):
    LOG.info("Processing command '%s' from %s", command, get_message_author_username(message))
    target_message = resolve_command_target_message(message)
    reply_randomly(message.chat, target_message, command_to_reply_map[command])
    if target_message != message and is_administrator(message.chat):
        bot.delete_message(message.chat.id, message.message_id)


@bot.message_handler(func=lambda m: True, content_types=bot_utils.content_type_media)
def fallback_handler(message):
    command = bot_utils.extract_command(message.text)
    if not command:
        save_to_history(message)
    if command and command in configured_commands:
        handle_user_command(command, message)
        return
    if message.content_type == 'sticker' \
            and is_dev_mode_enabled() \
            and is_direct_message(message):
        # print sticker details to be added to config json
        sticker = message.sticker
        bot.reply_to(message, '{"content":"' + sticker.file_id + '"", "contentType":"sticker", "description":"'
                     + sticker.emoji + ' from ' + sticker.set_name + '"},')
        return
    reply_if_mentioned(message)


bot.infinity_polling()
