'''Command handlers for actions in groups'''

import logging
import re
import itertools
from pierogi.main import quote_database, BOT_USERNAME
from util.db_classes import QUOTE_TYPES
from util.util import with_session
from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, filters

# emoji definitions
LOUDLY_CRYING_FACE = '\U0001F62D'
POUTING_FACE = '\U0001F621'
SMILING_FACE_WITH_SUNGLASSES = '\U0001F60E'
SMILING_FACE_WITH_OPEN_MOUTH = '\U0001F603'
FROWNING_FACE = '\U00002639'
FAMILY_MAN_GIRL_BOY = '\U0001F468\U0000200D\U0001F467\U0000200D\U0001F466'
FLEXED_BICEPS = '\U0001F4AA'
VAMPIRE = '\U0001F9DB'
GRADUATION_CAP = '\U0001F393'


# possible command prefixes and their emojis
COMMAND_PREFIXES = {
    'add': None,
    'mad': POUTING_FACE,
    'sad': LOUDLY_CRYING_FACE,
    'rad': SMILING_FACE_WITH_SUNGLASSES,
    'glad': SMILING_FACE_WITH_OPEN_MOUTH,
    'bad': FROWNING_FACE,
    'dad': FAMILY_MAN_GIRL_BOY,
    'chad': FLEXED_BICEPS,
    'vlad': VAMPIRE,
    'grad': GRADUATION_CAP,
}

# possible command suffixes
COMMAND_SUFFIXES = ['quote', 'qoute']


def format_response(s, emoji):
    '''
    Insert an emoji into every space in a string

    :param str s: string to be formatted
    :param str emoji: emoji to be inserted into s
    :return: newly formatted s
    :rtype: s
    '''
    if emoji is not None:
        return f' {emoji} '.join(s.split(' '))
    return s


def generate_commands():
    '''
    Generate a list of possible commands from prefixes and suffixes

    :return: all possible combinations of command prefixes and suffixes
    :rtype: str
    '''
    return list(map(''.join, list(itertools.product(COMMAND_PREFIXES.keys(), COMMAND_SUFFIXES))))


@with_session
async def handle_addquote(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        session: Session):
    '''Add a new quote to the database'''
    logging.info('addquote')
    logging.info(session)

    message = update.message
    quoted_message = message.reply_to_message

    # isolate command name
    command_text = re.split('/|@| ', message.text, 2)[1]

    # find prefix
    for prefix in COMMAND_PREFIXES:
        if command_text.startswith(prefix):
            command_prefix = prefix
            break

    # determine noun, verb, and emoji for given command
    if command_prefix is not None:
        noun = command_text[len(command_prefix):]
        verb = f'{command_prefix}ded'.replace('ddd', 'dd')
        emoji = COMMAND_PREFIXES[command_prefix]
    else:
        noun = 'quote'
        verb = 'added'
        emoji = None

    if quoted_message.forward_from_message_id is not None:  # prevent quoting automatic channel forwards
        response = f"can't {noun} auto-forwarded channel posts"
    else:
        # determine quote type
        if quoted_message.photo and not quoted_message.sticker:
            # found photo quote
            message_type = QUOTE_TYPES.PHOTO.value

            # choose largest photo TODO: quote multiple photos?
            photo = list(reversed(sorted(quoted_message.photo, key=lambda p: p.width * p.height)))

            content = quoted_message.caption
            content_html = quoted_message.caption_html
            file_id = photo.file_id
        elif quoted_message.text is not None:
            # found text quote
            message_type = QUOTE_TYPES.TEXT.value

            content = quoted_message.text
            content_html = quoted_message.text_html
            file_id = None
        else:
            # can't quote things that arent photos or text
            message_type = None
            response = f"can only {noun} text and/or photo messages"

        # extract necessary quote information if we have a valid quote type
        if message_type is not None:
            chat_id = message.chat_id
            message_id = quoted_message.message_id
            quoted_by = message.from_user
            quoted_by_id = quoted_by.id
            quoted_at = message.date
            is_forward = quoted_message.forward_from is not None
            if is_forward:
                forwarded_by = quoted_message.from_user
                forwarded_by_id = forwarded_by.id
                forwarded_at = quoted_message.date
                sent_by = quoted_message.forward_from
                sent_by_id = sent_by.id
                sent_at = quoted_message.forward_date
            else:
                forwarded_by = None
                forwarded_by_id = None
                forwarded_at = None
                sent_by = quoted_message.from_user
                sent_by_id = sent_by.id
                sent_at = quoted_message.date

            # if sent_by.username == BOT_USERNAME.lstrip('@'):  # prevent quoting bot messages
            #     response = f"can't {noun} this bot's messages"
            if sent_by_id == quoted_by_id:  # prevent quoting own messages
                response = f"can't {noun} your own messages"
            else:
                # add or update relevant users to db
                quote_database.add_or_update_user(session, sent_by)
                quote_database.add_or_update_user(session, quoted_by)
                quote_database.add_or_update_user(session, forwarded_by)

                # attempt to add quote to database
                new_quote, status = quote_database.add_quote(
                    session, chat_id, message_id, is_forward, forwarded_by_id, forwarded_at, sent_by_id, sent_at,
                    message_type, content, content_html, file_id, quoted_by_id, quoted_at)

                # check if quote was added successfully
                if status == quote_database.QUOTE_SUCCESSFULLY_ADDED:
                    response = f'{noun} {verb}'
                elif status == quote_database.QUOTE_ALREADY_EXISTS:
                    response = f'{noun} already exists'
                elif status == quote_database.QUOTE_PREVIOUSLY_DELETED:
                    response = f'{noun} was previously deleted'
                else:
                    response = 'invalid quote status found'
                    raise RuntimeError(
                        f'invalid quote add status found: {status}')

    # reply to user with result
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=format_response(response, emoji),
        reply_to_message_id=message.message_id)

handler_addquote = CommandHandler(
    generate_commands(),
    handle_addquote,
    filters.ChatType.GROUPS & filters.REPLY)
