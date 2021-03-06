import json
import os.path
import sys
from shutil import copy

import telebot
from telebot import util as bot_utils

import logger
import replies_history as rh_module
import reply_settings_utils
import chat_utils
import message_utils
import meme_utils
from check_admin import AdminPermissionsChecker
from developer import DevMode
from messages_history import MessagesHistory
from reply import Replier

LOG = logger.LOG

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

messages_history = MessagesHistory()
replies_history = rh_module.RepliesHistory(replies_settings)
replier = Replier(bot, replies_settings, replies_history)
dev_mode = DevMode(settings, bot)
admin_permissions_checker = AdminPermissionsChecker(bot, bot_details)


def write_settings_to_file():
    with open(settings_file_path, 'w', encoding=settings_file_encoding) as outfile:
        json.dump(settings, outfile)
    LOG.info('Settings file updated.')


def strong_reply(original_message, message_to_reply):
    replier.reply_randomly(original_message.chat, 'strongReply', message_to_reply)


def check_if_message_from_developer(message):
    return message_utils.get_message_author_username(message) in developer_usernames


def handle_if_message_from_developer(message, handler):
    if check_if_message_from_developer(message):
        handler(message)
    else:
        bot.reply_to(message, 'You are not my master!')
        strong_reply(message, message)


def reply_if_mentioned(message):
    self_username = bot_details.username
    replied_to_us = message_utils.is_replied_to(message, self_username)
    mentioned = message_utils.is_mentioned(message, self_username)
    LOG.debug('Handling: replied_to_us=%s, mentioned=%s', replied_to_us, mentioned)
    if not replied_to_us and not mentioned:
        LOG.debug('Message ignored: %s', message)
        return  # not our business
    if dev_mode.is_strong_reply_allowed() and mentioned:
        msg_to_reply = message_utils.get_reply_to_message(message)
        strong_reply(message, msg_to_reply if msg_to_reply else message)
        return
    if dev_mode.is_simple_reply_allowed() and replied_to_us:
        replier.reply_randomly(message.chat, 'simpleReply', message)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "What's up? Check my repo 'https://github.com/MrUpyachka/bothometh'")


@bot.message_handler(commands=['toggle_dev_mode'])
def toggle_dev_mode_on_command(message):
    handle_if_message_from_developer(message, dev_mode.toggle_dev_mode)


@bot.message_handler(commands=['toggle_reactions'])
def toggle_reactions_on_command(message):
    handle_if_message_from_developer(message, lambda _: dev_mode.toggle_reactions())


@bot.message_handler(commands=['save'])
def trigger_settings_save(message):
    handle_if_message_from_developer(message, lambda m: write_settings_to_file())


@bot.message_handler(commands=["meme"])
def memes_from_reddit(message):
    meme = meme_utils.get_reddit_meme()
    if meme is None:
        bot.send_message(message.chat.id, 'No memes :(')
    else:
        title = meme['title']
        image = meme['url']
        bot.send_photo(message.chat.id, image, caption=title)


def mention_user(chat, username):
    message = bot.send_message(chat.id, '@' + username)
    LOG.debug('User %s mentioned in chat %s (%s)', username, chat.id, chat.title)
    return message


def resolve_command_target_message(message):
    msg_to_reply = message_utils.get_reply_to_message(message)
    if msg_to_reply:
        return msg_to_reply
    target_user = message_utils.get_mentioned_username(message)
    if target_user:
        target_user_message = messages_history.get_last_message_of(target_user, message.chat)
        if not target_user_message:
            mention_user(message.chat, target_user)
            return None
        return target_user_message
    return message


def handle_user_command(command, message):
    LOG.info("Processing command '%s' from %s", command, message_utils.get_message_author_username(message))
    target_message = resolve_command_target_message(message)
    replier.reply_randomly(message.chat, command_to_reply_map[command], target_message)
    if target_message != message and admin_permissions_checker.is_administrator(message.chat):
        bot.delete_message(message.chat.id, message.message_id)


def update_replies_with_generated_ids():
    for replies_set_ref in replies_settings:
        for reply in replies_settings[replies_set_ref]:
            if 'id' not in reply:
                reply['id'] = hash(reply_settings_utils.extract_reply_content(reply))


def handle_new_participant(message):
    participant = message_utils.get_attribute_from_message_json(message, 'new_chat_participant')
    mention_user(message.chat, participant['username'])
    replier.reply_randomly(message.chat, command_to_reply_map['hello'])


@bot.message_handler(func=lambda m: True, content_types=(bot_utils.content_type_media + bot_utils.content_type_service))
def fallback_handler(message):
    command = bot_utils.extract_command(message.text)
    if not command:
        messages_history.save(message)
    if command and command in configured_commands:
        handle_user_command(command, message)
        return
    if message.content_type == 'new_chat_members':
        handle_new_participant(message)
        return
    if message.content_type == 'sticker' \
            and dev_mode.is_dev_mode_enabled() \
            and chat_utils.is_private(message.chat):
        # print sticker details to be added to config json
        sticker = message.sticker
        bot.reply_to(message, '{"content":"' + sticker.file_id + '", "contentType":"sticker", "description":"'
                     + sticker.emoji + ' from ' + sticker.set_name + '"},')
        return
    reply_if_mentioned(message)


update_replies_with_generated_ids()
bot.infinity_polling()
