from operator import or_
from functools import reduce

import reply_settings_utils


class RepliesSettings:
    def __init__(self, settings):
        self.command_to_reply_map = settings['commandToReplies']
        self.replies_map = settings['replies']
        self.configured_commands = self.command_to_reply_map.keys()
        self.configured_sets = self.replies_map.keys()
        self.configured_aliases = reduce(or_, [self.configured_commands, self.configured_sets])

    def get_replies_set(self, ref):
        if ref in self.configured_commands:
            return self.command_to_reply_map[ref]
        if ref in self.configured_sets:
            return self.replies_map[ref]
        return None

    def is_configured(self, alias):
        return alias in self.configured_aliases

    def update_replies_with_generated_ids(self):
        for replies_set_ref in self.replies_map:
            for reply in self.replies_map[replies_set_ref]:
                if 'id' not in reply:
                    reply['id'] = hash(reply_settings_utils.extract_reply_content(reply))
