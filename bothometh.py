import json
import random

import requests
import telebot
import logging
import sys


logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)

LOG = logging


class BotSettings:
    def __init__(self, username, developer_username, dev_mode_enabled):
        self.username = username
        self.developer_username = developer_username
        self.dev_mode_enabled = dev_mode_enabled
        self.mentioned_key = '@' + username
        self.reply_stickers = []
        self.fuck_you_stickers = []


args = sys.argv
key = sys.argv[1]
bot = telebot.TeleBot(key)
bot_details = bot.get_me()
LOG.debug('Bot details retrieved: %s', bot_details)
settings = BotSettings(bot_details.username, 'upyach', False)


def extract_stickers_set(stickers_config_json, set_name):
    """Loads sticker ID's for specified set-name from config"""
    stickers = []
    for sticker in stickers_config_json[set_name]:
        stickers.append(sticker['file_id'])
    return stickers


def update_stickers_set(set_collection, actual_stickers_set):
    """Resets existing stickers collection and fills it with new stickers"""
    set_collection.clear()
    set_collection.extend(actual_stickers_set)


def load_stickers_config():
    """Loads all stickers sets"""
    stickers_config = ''.join(open('./stickers.json', 'r', encoding='utf-8').readlines())
    stickers_config_json = json.loads(stickers_config)
    update_stickers_set(settings.fuck_you_stickers, extract_stickers_set(stickers_config_json, 'FUCK_YOU_STICKERS'))
    update_stickers_set(settings.reply_stickers, extract_stickers_set(stickers_config_json, 'JUST_REPLY_STICKERS'))
    LOG.debug('%d stickers found to fuck someone', len(settings.fuck_you_stickers))
    LOG.debug('%d stickers found to reply on anything', len(settings.reply_stickers))


def select_random(*args):
    """Returns randomly selected argument"""
    return args[random.randint(0, len(args) - 1)]


def are_we_mentioned(message):
    """Checks that bot mentioned in specified message"""
    if not hasattr(message, 'json'):
        return False
    json_val = message.json
    if 'entities' not in json_val:
        return False
    entities = json_val['entities']
    if entities:
        for ent in entities:
            if ent['type'] == 'mention' and settings.mentioned_key in json_val['text']:
                return True
    return False


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


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "What's up?")


@bot.message_handler(commands=['toggle_dev_mode'])
def toggle_dev_mode(message):
    settings.dev_mode_enabled = not settings.dev_mode_enabled
    LOG.info('Dev mode switched by chat command: %s', 'enabled' if settings.dev_mode_enabled else 'disabled')


@bot.message_handler(content_types=["sticker"])
def reply_sticker(message):
    LOG.debug('Sticker received with message: %s', message)
    if settings.dev_mode_enabled and get_message_author_username(message) == settings.developer_username:
        stk = message.sticker
        bot.reply_to(message, '{"file_id":"' + stk.file_id + '", "description":"'
                     + stk.emoji + ' from ' + stk.set_name + '"},')


@bot.message_handler(content_types=["text"])
def reply_mention(message):
    replied_to_us = is_replied_to_us(message)
    mentioned = are_we_mentioned(message)
    if not replied_to_us and not mentioned:
        LOG.debug('Message ignored: %s', message)
        return  # not our business
    if not replied_to_us and mentioned:
        msg_to_reply = get_reply_to_message(message)
        bot.send_sticker(message.chat.id, select_random(*settings.fuck_you_stickers),
                         message.message_id if msg_to_reply is None else msg_to_reply.message_id)
        return
    # just random response otherwise
    random_tuple = select_random(
        # (bot.send_message, reply),  # send random text reply
        (bot.send_sticker, settings.reply_stickers))  # send random sticker from set
    random_tuple[0](message.chat.id, select_random(*random_tuple[1]), message.message_id)


load_stickers_config()

while True:
    try:
        LOG.info('Updates polling started...')
        bot.polling()
        LOG.info('Interrupted by user or system.')
        break
    except requests.exceptions.ReadTimeout:
        LOG.info('Read time-out exception. Try again...')
    except Exception as e:
        LOG.error('Unknown exception: %s', e)
        break
