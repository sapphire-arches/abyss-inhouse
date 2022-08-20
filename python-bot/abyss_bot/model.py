import discord
from sqlalchemy import *
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    # Internal ID number
    id = Column(Integer, primary_key=True)
    # Discord Snowflake ID
    discord_id = Column(BigInteger)
    # Discord username
    discord_username = Column(String)
    # Whether the user is currently subscribed
    subscriber = Column(Boolean, nullable=False)
    # Whether the user is a VIP
    vip = Column(Boolean, nullable=False)
    # Whether the user is a bot admin
    bot_admin = Column(Boolean, default=False, nullable=False)

    # Relationship for looking up the queue entry for this user
    queue_entry = relationship('QueueEntry', back_populates='user')

    games = relationship('GamePlayer', back_populates='user')

    __table_args__ = (
        UniqueConstraint('discord_id'),
    )

    def __repr__(self):
        return f'User(id={self.id!r}, discord_id={self.discord_id!r}, discord_username={self.discord_username!r}, subscriber={self.subscriber!r}, vip={self.vip!r}, bot_admin={self.bot_admin!r})'

class QueueEntry(Base):
    __tablename__ = 'queue'

    # ID for this entry in the queue, in case we end up needing that
    id = Column(Integer, primary_key=True)
    # User for which this queue entry is created
    # Each user may have only 1 entry in the queue
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    # Time at which this entry in the queue was created
    enroll_time = Column(DateTime)
    # Whether this queue entry has been used
    serviced = Column(Boolean, default=False, nullable=False)

    user = relationship('User', back_populates='queue_entry')

    def __repr__(self):
        return f'QueueEntry(id={self.id!r}, user_id={self.user_id!r}, enroll_time={self.enroll_time!r})'

class Game(Base):
    __tablename__ = 'game'

    # Primary identifier for this actual game
    id = Column(Integer, primary_key=True)

    # Role managed for this game
    role_id = Column(BigInteger)

    # Channel managed for this game
    channel_id = Column(BigInteger)

    # Dota2 game ID
    dota2_match_id = Column(Integer)

    players = relationship('GamePlayer', back_populates='game')

class GamePlayer(Base):
    __tablename__ = 'game_player'

    # ID for this player in a particular game
    id = Column(Integer, primary_key=True)

    # Game the user played in
    game_id = Column(Integer, ForeignKey('game.id'), nullable=False)
    # User that played in the game
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    # Whether the user has been removed from the game
    removed = Column(Boolean, default=False, server_default='FALSE', nullable=False)

    game = relationship('Game', back_populates='players')

    user = relationship('User', back_populates='games')

#===============================================================================
# utilities
#===============================================================================
def get_db_user(session, user: discord.User):
    """ Get a DB user from a discord.User object """
    return session.execute(
        select(User).filter_by(discord_id=user.id)
    ).scalar_one_or_none()
