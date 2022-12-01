'''Classes for defining the quote databse schema'''

from enum import Enum
from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, PrimaryKeyConstraint, String, Text,
    UniqueConstraint)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.schema import Table

Base = declarative_base()


# enums
class CHAT_TYPES(Enum):
    '''Telegram chat types'''
    GROUP = 'GROUP'
    SUPERGROUP = 'SUPERGROUP'
    CHANNEL = 'CHANNEL'
    PRIVATE = 'PRIVATE'


class QUOTE_TYPES(Enum):
    '''Types of messages that can be quoted'''
    TEXT = 'TEXT'
    PHOTO = 'PHOTO'


# defines who is in what chat. maybe track admin perms here?
chat_membership_table = Table(
    'chat_membership',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('chat_id', Integer, ForeignKey('chat.id')),
    PrimaryKeyConstraint('user_id', 'chat_id'))


class User(Base):
    '''Any user who belongs to a chat'''
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String)
    username = Column(String, unique=True, nullable=False)

    chats = relationship(
        'Chat',
        secondary=chat_membership_table,
        back_populates='users')
    quotes_authored = relationship(
        'Quote',
        back_populates='sent_by',
        foreign_keys='Quote.sent_by_id')
    quotes_added = relationship(
        'Quote',
        back_populates='quoted_by',
        foreign_keys='Quote.quoted_by_id')
    quotes_forwarded = relationship(
        'Quote',
        back_populates='forwarded_by',
        foreign_keys='Quote.forwarded_by_id')
    votes = relationship(
        'Vote',
        back_populates='user')


class Chat(Base):
    '''Any group or supergroup in which the bot is a member'''
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True, autoincrement=False)
    type = Column(SQLEnum(CHAT_TYPES), nullable=False)
    title = Column(String)

    users = relationship(
        'User',
        secondary=chat_membership_table,
        back_populates='chats')
    quotes = relationship(
        'Quote',
        back_populates='chat')
    sent_quote_messages = relationship(
        'SentQuoteMessage',
        back_populates='chat')


class Quote(Base):
    '''A message that's been quoted by the bot'''
    __tablename__ = 'quote'

    id = Column(Integer, primary_key=True, autoincrement=True)

    chat_id = Column(Integer, ForeignKey('chat.id'))
    chat = relationship(
        'Chat',
        back_populates='quotes')

    sent_by_id = Column(Integer, ForeignKey('user.id'))
    sent_by = relationship(
        'User',
        back_populates='quotes_authored',
        foreign_keys=[sent_by_id])

    forwarded_by_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    forwarded_by = relationship(
        'User',
        back_populates='quotes_forwarded',
        foreign_keys=[forwarded_by_id])

    quoted_by_id = Column(Integer, ForeignKey('user.id'))
    quoted_by = relationship(
        'User',
        back_populates='quotes_added',
        foreign_keys=[quoted_by_id])

    message_id = Column(Integer)
    is_forward = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    forwarded_at = Column(DateTime, nullable=True)
    quoted_at = Column(DateTime, nullable=True)
    content = Column(Text)
    content_html = Column(Text)
    file_id = Column(String)
    message_type = Column(SQLEnum(QUOTE_TYPES), default='text')
    deleted = Column(Boolean, default=False)
    score = Column(Integer, default=0)

    sent_quote_messages = relationship(
        'SentQuoteMessage',
        back_populates='quote')
    votes = relationship(
        'Vote',
        back_populates='quote')

    constraint1 = UniqueConstraint('chat_id', 'message_id')
    constraint2 = UniqueConstraint('sent_at', 'sent_by_id', 'content_html')


class SentQuoteMessage(Base):
    '''A message sent by the bot that contains a quote as a result'''
    __tablename__ = 'sent_quote_message'

    id = Column(Integer, primary_key=True, autoincrement=True)

    chat_id = Column(Integer, ForeignKey('chat.id'))
    chat = relationship(
        'Chat',
        back_populates='sent_quote_messages')

    quote_id = Column(Integer, ForeignKey('quote.id'), nullable=True)
    quote = relationship(
        'Quote',
        back_populates='sent_quote_messages')

    message_id = Column(Integer)


class Vote(Base):
    '''A vote cast by a user on a specific quote'''
    __tablename__ = 'vote'

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    user = relationship(
        'User',
        back_populates='votes')

    quote_id = Column(Integer, ForeignKey('quote.id'), nullable=True)
    quote = relationship(
        'Quote',
        back_populates='votes')

    direction = Column(Integer, default=0, nullable=False)

    constraint1 = UniqueConstraint('user_id', 'quote_id')
