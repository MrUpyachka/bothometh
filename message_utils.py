import chat_utils


def get_message_author_username(message):
    from_user = message.from_user
    if from_user is None or not hasattr(from_user, 'username'):
        return None
    return from_user.username


def get_reply_to_message(message):
    """Returns ID of message specified message replies to"""
    if not hasattr(message, 'reply_to_message'):
        return None
    reply_to_message = message.reply_to_message
    if reply_to_message is None or not hasattr(reply_to_message, 'message_id'):
        return None
    return reply_to_message


def get_message_json(message):
    if not hasattr(message, 'json'):
        return None
    return message.json


def get_attribute_from_message_json(message, attribute):
    json_val = get_message_json(message)
    if not json_val:
        return None
    if attribute not in json_val:
        return None
    return json_val[attribute]


def get_message_entities(message):
    return get_attribute_from_message_json(message, 'entities')


def get_mentioned_username(message):
    entities = get_message_entities(message)
    if not entities:
        return None
    for ent in entities:
        if ent['type'] == 'mention':
            text = get_attribute_from_message_json(message, 'text')
            # offset increased to remove @ sign
            start_position = ent['offset'] + 1
            mention_length = ent['length']
            return text[start_position:start_position + mention_length]
    return None


def is_replied_to(message, username):
    """Checks that message replies to our own message"""
    reply_to_message = get_reply_to_message(message)
    if reply_to_message is None:
        return False
    if get_message_author_username(reply_to_message) == username:
        return True
    return False


def is_mentioned(message, username):
    if chat_utils.is_private(message.chat):
        return True
    entities = get_message_entities(message)
    if not entities:
        return False
    for ent in entities:
        if ent['type'] == 'mention' and username in get_message_json(message)['text']:
            return True
    return False
