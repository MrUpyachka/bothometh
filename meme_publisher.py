import random
import praw
import logger

LOG = logger.LOG


class MemePublisher:
    def __init__(self, reddit_client_id, reddit_client_secret, reddit_client_user_agent):
        self.reddit = praw.Reddit(client_id=reddit_client_id,
                                  client_secret=reddit_client_secret,
                                  user_agent=reddit_client_user_agent)
        self.topic = 'meme'
        self.query = 'bonk OR horny OR hornyjail OR waifu'
        self.meme_list = []

    def refresh_memes(self):
        LOG.info("No more memes, getting new ones...")
        sub_reddit = self.reddit.subreddit(self.topic)\
            .search(self.query, sort="top", limit=200)
        self.meme_list = list(sub_reddit)
        if len(self.meme_list) == 0:
            LOG.info("No memes found")
            self.meme_list.append(None)
        else:
            LOG.info("Got %s memes", len(self.meme_list))
            random.shuffle(self.meme_list)

    def get_reddit_meme(self):
        if len(self.meme_list) == 0:
            self.refresh_memes()
        meme = self.meme_list.pop()
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
