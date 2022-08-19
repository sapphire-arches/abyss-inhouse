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
from . import views
from .client import AbyssClient
from .config import config
from .model import get_db_user

logger = logging.getLogger(__name__)

#===============================================================================
# Guild config
#===============================================================================

# Mapping from internal name to whatever the guild actually names the roles
ROLE_NAMES = {
    'VIP': config.get('guild', 'role.vip', fallback='VIP'),
    'SUB': config.get('guild', 'role.sub', fallback='SUB'),
}

#===============================================================================
# Client definition
#===============================================================================

intents = discord.Intents.default()
client = AbyssClient(intents=intents)

#===============================================================================
# Handy queries
#===============================================================================
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
            db_user = get_db_user(session, user)

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
                db_user.vip |= user.get_role(role_vip.id) is not None
            else:
                # VIPs are manually tagged if there is no VIP role
                pass

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
                content=f'Added <@{user.id}> to the queue. Use /list_abyss to see the current queue'
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

def render_list(it):
    str = ''

@client.tree.command(
    description='View the current queue for the abyss'
)
async def list_abyss(interaction: discord.Interaction):
    await views.respond_with_view(client, interaction, False)

@client.tree.command(
    description='List the queue starting from non-subscribers'
)
async def list_skrub(interaction: discord.Interaction):
    await views.respond_with_view(client, interaction, True)

@client.tree.command(
    description='Pop an entry from the queue'
)
async def pop(interaction: discord.Interaction, user: discord.User):
    with client.sm.begin() as session:
        db_user = get_db_user(session, interaction.user)

        if db_user is None or not db_user.bot_admin:
            await interaction.response.send_message(
                content=f'You are not authorized to remove people from the queue',
                ephemeral=True
            )
            return

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
        db_user = get_db_user(session, interaction.user)

        if db_user is None or not db_user.bot_admin:
            await interaction.response.send_message(
                content=f'You are not authorized to clear the queue',
                ephemeral=True
            )
            return
        session.execute(clear_queue_stmt)

    await interaction.response.send_message(
        content="The Abyss has been restarted."
    )


from . import game
client.tree.add_command(game.GAME)

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
    logging.info('Begin bot startup')
    token = get_env('DISCORD_TOKEN')
    db_client_string = get_env('DB_CLIENT_STRING')

    logging.info('SQLAlchemy engine construction')
    client.engine = sa.create_engine(db_client_string, future=True)
    client.sm = sessionmaker(client.engine, future=True)

    loop = asyncio.get_running_loop()

    def sigterm_to_keyboardint():
        raise KeyboardInterrupt("SIGTERM recieved")

    loop.add_signal_handler(signal.SIGTERM, sigterm_to_keyboardint)

    try:
        logging.info('Bot login')
        await client.login(token)
        logging.info('Bot boot')
        await client.connect()

        # TODO: in parallel, we should kick off a process that pings the DB
        # every ~60 seconds and reconiles the DB and discord states (instead of
        # add-hoc sub role sync / game channel management).
    except Exception as e:
        logger.error('Bot exploded', exc_info=e)

asyncio.run(main())
