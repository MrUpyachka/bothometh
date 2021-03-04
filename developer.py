from logger import LOG
from telebot import TeleBot


class DevMode:
    def __init__(self, settings, bot: TeleBot):
        self.settings = settings
        self.bot = bot

    def toggle_dev_mode(self, message):
        mode = not self.settings['devModeEnabled']
        self.settings['devModeEnabled'] = mode
        LOG.info('Dev mode switched by chat command: %s', 'enabled' if mode else 'disabled')
        if mode:
            self.bot.reply_to(message, 'Send a sticker to direct - I will provide you its code.')

    def toggle_reactions(self):
        mode = not self.settings['simpleReplyEnabled']
        self.settings['simpleReplyEnabled'] = mode
        self.settings['strongReplyEnabled'] = mode
        LOG.info('Reactions mode switched by chat command: %s', 'enabled' if mode else 'disabled')

    def is_simple_reply_allowed(self):
        return self.settings['simpleReplyEnabled']

    def is_strong_reply_allowed(self):
        return self.settings['strongReplyEnabled']

    def is_dev_mode_enabled(self):
        return self.settings['devModeEnabled']
