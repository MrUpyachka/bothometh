import collections

import random
from logger import LOG


def select_random(choices):
    return random.choice(choices)


def calculate_replies_history_size(replies_set):
    replies_number = len(replies_set)
    percentage = int(replies_number * 0.6)
    if (replies_number - percentage) < 2:
        # to avoid cycling between two replies
        return 0
    return percentage


class RepliesHistory:
    def __init__(self, replies_settings):
        self.replies_settings = replies_settings
        self.replies_history = {}

    def get_recently_used_replies_ids(self, replies_set_ref):
        if replies_set_ref in self.replies_history:
            return self.replies_history[replies_set_ref]
        if replies_set_ref not in self.replies_settings:
            LOG.debug("Unable to get replies usage history for '%s'", replies_set_ref)
            return None
        history_length = calculate_replies_history_size(self.replies_settings[replies_set_ref])
        replies_set_history = collections.deque([], history_length)
        self.replies_history[replies_set_ref] = replies_set_history
        return replies_set_history

    def update_recently_used_replies(self, replies_set_ref, reply):
        self.get_recently_used_replies_ids(replies_set_ref).append(reply['id'])

    def select_not_recently_used(self, replies_set_ref):
        replies_set = self.replies_settings[replies_set_ref]
        if not replies_set:
            LOG.info("No replies available for %s", replies_set_ref)
            return None
        recently_used_replies = self.get_recently_used_replies_ids(replies_set_ref)
        available_replies = list(filter(lambda r: r['id'] not in recently_used_replies, replies_set))
        if not available_replies:
            LOG.info("All replies are in list of recently used for '%s'", replies_set_ref)
            return None
        return select_random(available_replies)
