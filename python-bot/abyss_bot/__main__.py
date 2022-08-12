from discord import app_commands
from discord.ext import commands
from discord.utils import get
import asyncio
import discord
import logging
import os
import random
import signal
import string
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from . import model

#===============================================================================
# Logger setup
#===============================================================================

logging.basicConfig(level=logging.INFO)
logging.getLogger('asyncio').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.orm').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.pool').setLevel(logging.INFO)

logger = logging.getLogger('abyss-bot')
logger.setLevel(level=logging.INFO)

#===============================================================================
# Config
#===============================================================================

# Guild hard-coded to abyss-dev for now
GUILDS = [
    1000819141596414002, # abyss-dev
    909167831302680617, # Twitch Stuff
]
INHOUSE_CHANNEL_ID = 1000819141596414005
ROLES_CHANNEL_ID = 1006837412787388457
ROLES_MESSAGE_ID = 1006837453870608435

# Mapping from internal name to whatever the guild actually names the roles
ROLE_NAMES = {
    'VIP': 'VIP',
    'SUB': 'SUB',
}

#===============================================================================
# Client definition
#===============================================================================
class AbyssClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        for guild in GUILDS:
            guild=discord.Object(id=guild)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

intents = discord.Intents.default()
client = AbyssClient(intents=intents)

#===============================================================================
# Handy queries
#===============================================================================
get_queue_stmt = (sa
    .select(model.QueueEntry, model.User)
    .filter_by(serviced=False)
    .join(model.QueueEntry.user)
    .order_by(
        model.User.vip,
        model.User.subscriber,
        model.QueueEntry.enroll_time,
    ))

clear_queue_stmt = (sa
    .update(model.QueueEntry)
    .where(model.QueueEntry.serviced == False)
    .values(serviced=True))

#===============================================================================
# global state
# TODO: persist this to postgresql
#===============================================================================

TeamCompV = 0
TeamCompS = 5
TeamCompNS = 0

#===============================================================================
# Client event handlers
#===============================================================================
@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user} (ID: {client.user.id})')

#===============================================================================
# Commands
#===============================================================================

@client.tree.command(
    description='Join the queue for the abyss inhouse'
)
async def join_abyss(interaction: discord.Interaction):
    global FullList, FullListVIP, FullListNonSub
    global Queue, QueueVIP, QueueNonSub
    # TODO: require steam ID to join
    user = interaction.user

    role_vip = None
    role_sub = None

    with client.sm.begin() as session:
        db_user = session.execute(sa.select(model.User).filter_by(discord_id=user.id)).scalar_one_or_none()

        if db_user is None:
            db_user = model.User(
                discord_id=user.id,
            )
            session.add(db_user)

        db_user.discord_username = user.name

        for role in interaction.guild.roles:
            if role.name == ROLE_NAMES['VIP']:
                role_vip = role
            elif role.name == ROLE_NAMES['SUB']:
                role_sub = role

        db_user.vip = user.get_role(role_vip.id) is not None
        db_user.subscriber = user.get_role(role_sub.id) is not None

        # Make sure the user is up to date
        session.flush()

        queue_entry = session.execute(
            sa.select(model.QueueEntry)
                .filter_by(user_id=db_user.id, serviced=False)
                .order_by(model.QueueEntry.enroll_time.asc())
                .limit(1)
        ).scalar_one_or_none()

        if queue_entry is None:
            queue_entry = model.QueueEntry(
                user_id=db_user.id,
                enroll_time=sa.sql.functions.now(),
                serviced=False,
            )
            session.add(queue_entry)
        else:
            await interaction.response.send_message(
                content="You're already in the queue for today!",
                ephemeral=True
            )

        try:
            session.commit()
            await interaction.response.send_message(
                content=f'Added {user.name} to the queue. Use /list_abyss to see the current queue'
            )
        except sa.exc.IntegrityError:
            session.rollback()
            await interaction.response.send_message(
                content="You're already in the queue for today!",
                ephemeral=True
            )
        except discord.errors.InteractionResponded:
            # We probably already sent some sort of error message
            session.rollback()
            pass

@client.tree.command(
    description='View the current queue for the abyss'
)
async def list_abyss(interaction: discord.Interaction):
    str = 'Abyss inhouse queue:\n>>> '

    with client.sm.begin() as session:
        queue = session.execute(get_queue_stmt).all()
        for (i, (qe, user)) in enumerate(queue):
            str += f'{i+1} (entry {qe.id}). {user.discord_username}\n'
            if len(str) > 1500:
                str += '\n ... and more'
                break

    await interaction.response.send_message(
        content=str,
        ephemeral=True
    )

@client.tree.command(
    description='Pop an entry from the queue'
)
async def pop(interaction: discord.Interaction, user: discord.User):
    with client.sm.begin() as session:
        statement = (sa
            .select(model.QueueEntry)
            .join(model.QueueEntry.user)
            .filter(model.User.discord_id == user.id)
            .filter(model.QueueEntry.serviced == False))

        serviced = False
        for entry in session.execute(statement).scalars().all():
            serviced = True
            entry.serviced = True

    if serviced:
        await interaction.response.send_message(
            content=f'Removed {user.name} from the queue',
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            content=f'{user.name} appears to not be in the queue',
            ephemeral=True
        )

@client.tree.command(
    description='Clear all queues'
)
async def restart_abyss(interaction: discord.Interaction):
    with client.sm.begin() as session:
        session.execute(clear_queue_stmt)

    await interaction.response.send_message(
        content="The Abyss has been restarted."
    )

#===============================================================================
# asyncio loop execution
#===============================================================================
def get_env(name):
    val = os.getenv(name)
    if val is None:
        err = f'Missing {name} in the environment'
        logger.error(err)
        raise ValueError(err)
    return val

async def main():
    token = get_env('DISCORD_TOKEN')
    db_client_string = get_env('DB_CLIENT_STRING')

    client.engine = sa.create_engine(db_client_string, future=True)
    client.sm = sessionmaker(client.engine, future=True)

    loop = asyncio.get_running_loop()

    def sigterm_to_keyboardint():
        raise KeyboardInterrupt("SIGTERM recieved")

    loop.add_signal_handler(signal.SIGTERM, sigterm_to_keyboardint)

    try:
        await client.login(token)
        await client.connect()
    except Exception as e:
        logger.error('Bot exploded', exc_info=e)

asyncio.run(main())