import os
import random
import praw
import logger

LOG = logger.LOG

reddit = praw.Reddit(client_id=os.getenv("CLIENT_ID"),
                     client_secret=os.getenv("CLIENT_SECRET"),
                     user_agent=os.getenv("USER_AGENT")
                     )

topic = 'meme'
query = 'bonk OR horny OR hornyjail OR waifu OR thicc'
meme_list = []


def refresh_memes():
    global meme_list

    LOG.info("No more memes, getting new ones...")
    subreddit = reddit.subreddit(topic).search(query, sort="top", limit=200)
    meme_list = list(subreddit)

    if len(meme_list) == 0:
        LOG.info("No memes found")
        meme_list.append(None)
    else:
        LOG.info("Got %s memes", len(meme_list))
        random.shuffle(meme_list)


def get_reddit_meme():
    global meme_list

    if len(meme_list) == 0:
        refresh_memes()
    meme = meme_list.pop()

    if meme is None:
        return None
    else:
        _ = meme.preview
        result = {
            "code": 200,
            "post_link": meme.shortlink,
            "subreddit": topic,
            "title": meme.title,
            "url": meme.url,
            "ups": meme.ups,
        }
    return result
