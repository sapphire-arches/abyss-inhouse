from discord import app_commands
from discord.ext import commands
from discord.utils import get
import asyncio
import discord
import logging
import logging.config
import os
import random
import signal
import string
import sqlalchemy as sa
from configparser import ConfigParser
from sqlalchemy.orm import sessionmaker

from . import model

#===============================================================================
# Config loading
#===============================================================================
logging.basicConfig(level=logging.DEBUG)

config = ConfigParser()
config.read([
    '/config/bot.config',
    '/config/override.config',
])

#===============================================================================
# Logger setup
#===============================================================================
LOG_LEVELS = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
    "NOTSET": 0,
}

def setup_logging(cfg):
    LOGMOD = 'logging.mod.'
    base_level = LOG_LEVELS[cfg.get('logging', 'root_level')]
    fmt = cfg.get('logging', 'format', raw=True)

    # Initialize loggers with the root configuration
    loggers = {
        '': {
            'handlers': ['default'],
            'level': base_level,
            'propagate': False
        }
    }

    for section in cfg.sections():
        if not section.startswith(LOGMOD):
            continue
        module = section[len(LOGMOD):]
        logging.info(f'Load level for module {module}')
        loggers[module] = {
            'level': LOG_LEVELS[cfg[section]['level']],
            'handlers': ['default'],
            'propagate': False
        }

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
        'loggers': loggers,
        'handlers': {
            'default': {
                'level': 'DEBUG',
                'formatter': 'default',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            }
        },
        'formatters': {
            'default': {
                'format': fmt
            }
        }
    })

setup_logging(config)

logger = logging.getLogger(__name__)

#===============================================================================
# Guild config
#===============================================================================

BIND_GUILD = config.get('guild', 'id', fallback=None)

# Mapping from internal name to whatever the guild actually names the roles
ROLE_NAMES = {
    'VIP': config.get('guild', 'role.vip', fallback='VIP'),
    'SUB': config.get('guild', 'role.sub', fallback='SUB'),
}

#===============================================================================
# Client definition
#===============================================================================
class AbyssClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        if BIND_GUILD is not None:
            guild = discord.Object(id=int(BIND_GUILD))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

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
        model.User.vip.desc(),
        model.User.subscriber.desc(),
        model.QueueEntry.enroll_time.asc(),
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
        try:
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
                elif 'SUB' in role.name.upper():
                    role_sub = role

            if role_vip is not None:
                logging.warning('No VIP role found!')
                db_user.vip = user.get_role(role_vip.id) is not None
            else:
                db_user.vip = False

            if role_sub is not None:
                logging.warning('No SUB role found!')
                db_user.subscriber = user.get_role(role_sub.id) is not None
            else:
                db_user.subscriber = False

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
        except Exception as e:
            logging.error(f'Failed to load users', exc_info=e)
            raise e

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
            str += f'{i+1}. {user.discord_username}'

            if user.subscriber:
                str += ' (sub)'
            str += '\n'

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
