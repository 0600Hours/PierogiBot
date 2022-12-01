'''Command handlers for actions related to the functioning of the bot itself'''

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters


def handle_group_migration(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    '''Handle a group becoming a supergroup'''
    # if hasattr(update.message, 'migrate_to_chat_id'):
    #     # TODO: migrate to in db
    # elif hasattr(update.message, 'migrate_from_chat_id'):
    #     # TODO: migrate from in db
    return


handler_group_migration = MessageHandler(
    filters.StatusUpdate.MIGRATE,
    handle_group_migration
)
