import random

import praw
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import logger

LOG = logger.LOG
QUERY_PREFIX = 'meme '


class MemePublisher:
    def __init__(self, reddit_client_id, reddit_client_secret, reddit_client_user_agent, settings):
        self.reddit = praw.Reddit(client_id=reddit_client_id,
                                  client_secret=reddit_client_secret,
                                  user_agent=reddit_client_user_agent)
        self.topic = settings['topic']
        self.queries = settings['queries']
        self.memes_cache = {}

    def refresh_memes(self, query):
        LOG.info("No more memes, getting new ones...")
        sub_reddit = self.reddit.subreddit(self.topic) \
            .search(query, sort="top", limit=200)
        loaded_memes = list(sub_reddit)
        if len(loaded_memes) == 0:
            LOG.info("No memes found")
            self.memes_cache[query] = loaded_memes
        else:
            LOG.info("Got %s memes", len(loaded_memes))
            random.shuffle(loaded_memes)
            self.memes_cache[query] = loaded_memes
        return loaded_memes

    def get_query_memes_cache(self, query):
        if query in self.memes_cache:
            return self.memes_cache[query]
        return self.refresh_memes(query)

    def get_reddit_meme(self, query):
        query_memes_cache = self.get_query_memes_cache(query)
        meme = query_memes_cache.pop()
        if meme is None:
            return None
        else:
            _ = meme.preview
            result = {
                "code": 200,
                "post_link": meme.shortlink,
                "subreddit": self.topic,
                "title": meme.title,
                "url": meme.url,
                "ups": meme.ups,
            }
        return result

    def queries_markup(self):
        result = InlineKeyboardMarkup()
        result.row_width = len(self.queries)
        for query in self.queries:
            result.add(InlineKeyboardButton(query, callback_data=QUERY_PREFIX + query))
        return result
