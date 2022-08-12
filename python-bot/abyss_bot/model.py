from sqlalchemy import *
from sqlalchemy.orm import relationship, declarative_base

META = MetaData()
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
    subscriber = Column(Boolean)
    # Whether the user is a VIP
    vip = Column(Boolean)
    # Whether the user is a bot admin
    bot_admin = Column(Boolean)

    # Relationship for looking up the queue entry for this user
    queue_entry = relationship('QueueEntry', back_populates='user')

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
